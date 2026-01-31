"""
Run i3status modules and display its outputs in py3status.

Configuration parameters:
    format: display format for this module (default '{format_module}')
    format_module_separator: show separator if more than one (default ' ')
    general: specify settings for i3status general section
        (default {'colors': True, 'interval': 5})
    modules: specify a list of i3status modules and settings (dicts)
        plus 'format_module' with '{output}' placeholder (default [])

Format placeholders:
    {format_module} format for i3status modules

Examples:
```
# add i3status modules
# See `man i3status` for a full list of i3status configuration options.
# Not all of i3status configuration options will be supported or usable.
i3status {
    format_module_separator = "\?color=#666&show  \| "
    general = {'colors': True, 'interval': 5}
    modules = [
        {
            "name": "ipv6",
            "format_down": "",
            "format_module": "\?if=output [\?color=darkgrey&show IPv6] {output}",
        },
        {
            "name": "wireless _first_",
            "format_up": "(%quality at %essid) %ip",
            "format_down": "",
            "format_module": "\?if=output [\?color=darkgrey&show Wireless] {output}",
        },
        {
            "name": "ethernet _first_",
            "format_up": "%ip (%speed)",
            "format_down": "",
            "format_module": "\?if=output [\?color=darkgrey&show Ethernet] {output}",
        },
        {
            "name": "battery all",
            "format_module": "\?if=output [\?color=darkgrey&show Battery] {output}",
        },
        {
            "name": "disk /",
            "format": "%avail",
            "format_module": "[\?color=darkgrey&show Disk] {output}",
        },
        {
            "name": "load",
            "format": "%1min",
            "format_module": "[\?color=darkgrey&show Load] {output}",
        },
        {
            "name": "memory",
            "format": "%percentage_used",
            "format_module": "[\?color=darkgrey&show Memory] {output}",
        },
        {
            "name": "tztime local",
            "format": "%Y-%m-%d %H:%M:%S",
            "format_module": "[\?color=darkgrey&show Time] {output}",
        },
    ]
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'W: ( 86% at WiFi 5G)', 'color': '#00ff00'},
    {'full_text': ' | ', 'color': '#666'},
    {'full_text': 'E: down', 'color': '#ff0000'},
]

disk_tztime
]
    {'full_text': '1.2 TiB'}
    {'full_text': ' | ', 'color': '#666'},
    {'full_text': '2026-01-02 07:40:51 CST'}
[
"""

import json
from contextlib import suppress
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from tempfile import NamedTemporaryFile
from threading import Thread

MODULES = [
    {"name": "ipv6", "format_down": ""},
    {"name": "wireless _first_", "format_down": ""},
    {"name": "ethernet _first_", "format_down": ""},
    {"name": "battery all", "format_down": ""},
    {"name": "load", "format": "%1min"},
    {"name": "memory", "format": "%used"},
    {"name": "tztime local", "format": "%Y-%m-%d %H:%M:%S"},
]
SEPARATOR = r"\?color=#666&show  \| "
STRING_NOT_INSTALLED = "i3status not installed"


class Py3status:
    """ """

    # available configuration parameters
    format = "{format_module}"
    format_module_separator = " "
    general = {"colors": True, "interval": 5}
    modules = []

    def post_config_hook(self):
        if not self.py3.check_commands("i3status"):
            raise Exception(STRING_NOT_INSTALLED)
        if not self.modules:
            self.modules, self.format_module_separator = (MODULES, SEPARATOR)
        for module in self.modules:
            if not isinstance(module, dict) or not module.get("name"):
                raise Exception("invalid modules")
            module.setdefault("format_module", "{output}")

        self._write_i3status_config()
        self.i3status_command = ["i3status", "-c", self.tmpfile_name]
        self.error = None
        self.process = None
        self.running = True
        self.items = []
        self.line = ""

        self.t = Thread(target=self._start_loop)
        self.t.daemon = True
        self.t.start()

    def _write_i3status_config(self):
        def _format(value):
            if isinstance(value, bool):
                return f"{value}".lower()
            if isinstance(value, (int, float)):
                return f"{value}"
            return f'"{value}"'

        # fmt: off
        try:
            # python 3.12+
            tmpfile = NamedTemporaryFile(mode="w", encoding="utf-8", prefix="py3status-i3status_",
                suffix=".conf", delete=False, delete_on_close=False)
        except TypeError:
            tmpfile = NamedTemporaryFile(mode="w", encoding="utf-8", prefix="py3status-i3status_",
                suffix=".conf", delete=False)
        self.tmpfile_name = tmpfile.name
        # fmt: on

        lines = []
        general_settings = dict(self.general or {})
        general_settings.setdefault("output_format", "i3bar")
        lines.append("general {\n")
        for key, value in general_settings.items():
            lines.append(f"  {key} = {_format(value)}\n")
        lines.append("}\n\n")
        for module in self.modules:
            lines.append(f'order += "{module["name"]}"\n')
            lines.append(f'{module["name"]} {{\n')
            for key, value in module.items():
                if key in ("name", "format_module"):
                    continue
                lines.append(f"  {key} = {_format(value)}\n")
            lines.append("}\n\n")
        tmpfile.write("".join(lines))
        tmpfile.flush()
        tmpfile.close()

    def _parse_i3status_line(self, line):
        if not line or line in ["[", "]"] or line.startswith("{\"version\""):
            return None
        if line.startswith(","):
            line = line[1:]
        try:
            return json.loads(line)
        except ValueError:
            return None

    def _format_modules(self):
        new_items = []
        for item, module in zip(self.items, self.modules):
            if not item.get("full_text"):
                continue
            item.pop("name", None)
            item.pop("instance", None)
            new_items.append(self.py3.safe_format(module["format_module"], {"output": item}))
        return new_items

    def _cleanup(self):
        self.running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()
        with suppress(FileNotFoundError):
            Path(self.tmpfile_name).unlink()
        self.py3.update()

    def _start_loop(self):
        try:
            self.process = Popen(self.i3status_command, stdout=PIPE, stderr=STDOUT, text=True)
            while self.running:
                line = self.process.stdout.readline()
                if not line:
                    if self.process.poll() is not None:
                        raise Exception(self.line)
                    continue
                line = line.strip()
                items = self._parse_i3status_line(line)
                if items is None:
                    self.line = line
                    continue
                if items == self.items:
                    continue
                self.items = items
                self.py3.update()
        except Exception as err:
            self.error = " ".join(format(err).split()[1:])
        finally:
            self._cleanup()

    def i3status(self):
        if self.error:
            self.py3.error(self.error, self.py3.CACHE_FOREVER)

        format_module_separator = self.py3.safe_format(self.format_module_separator)
        format_module = self.py3.composite_join(format_module_separator, self._format_modules())

        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, {"format_module": format_module}),
        }

    def kill(self):
        self._cleanup()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
