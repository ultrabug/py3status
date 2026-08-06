r"""
Run i3status modules and display its outputs in py3status.

Configuration parameters:
    format: display format for this module (default '{format_module}')
    format_module_separator: show separator if more than one (default ' ')
    general: specify settings for i3status general section (default {})
    modules: specify a list of i3status modules and settings,
        optionally with `format_module` using `{output}`
        placeholder and update `interval` caching (default [])

Format placeholders:
    {format_module} format for i3status modules

Examples:
```
# add i3status options
# See `man i3status` for a full list of i3status configuration options.
# Not all of i3status configuration options will be supported or usable.
i3status {
    general = {
        'interval': 1   # update interval for i3status
        'colors': True  # enable/disable colors
    }
}

# add i3status modules
i3status {
    format_module_separator = "\?color=#666&show \|"
    modules = [
        {
            "name": "ipv6",
            "format_up": "%ip",
            "format_down": "",
            "format_module": "\?if=output [\?color=darkgrey&show IPv6] {output}",
        },
        {
            "name": "wireless _first_",
            "format_up": "%quality at %essid, %ip",
            "format_down": "",
            "format_quality": "%d%s",
            "format_module": "\?if=output [\?color=darkgrey&show Wireless] {output}",
            "interval": 10
        },
        {
            "name": "ethernet _first_",
            "format_up": "%ip",
            "format_down": "",
            "format_module": "\?if=output [\?color=darkgrey&show Ethernet] {output}",
        },
        {
            "name": "battery all",
            "format_module": "\?if=output [\?color=darkgrey&show Battery] {output}",
            "format_down": "",
        },
        {
            "name": "disk /",
            "format": "%avail",
            "format_module": "[\?color=darkgrey&show Disk] {output}",
            "interval": 60
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
             # "interval": 60
        },
        {
            "name": "cpu_temperature 0",
            "format": "%degrees°C",
            "format_module": "[\?color=darkgrey&show CPU Temp] {output}",
        }
    ]
    # Not all i3status modules are added here. See `man i3status` for more.
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
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired
from tempfile import NamedTemporaryFile
from threading import Thread
from time import monotonic


class Py3status:
    """ """

    # available configuration parameters
    format = "{format_module}"
    format_module_separator = " "
    general = {}
    modules = []

    def post_config_hook(self):
        if not self.py3.check_commands("i3status"):
            raise Exception("not installed")
        if not self.modules:
            raise Exception("missing 'modules' list")
        if not isinstance(self.modules, list):
            raise Exception("invalid 'modules': expected a list")

        interval = self.general.get("interval")

        for module in self.modules:
            if not isinstance(module, dict):
                raise Exception("invalid module: expected a dict")
            if not module.get("name"):
                raise Exception("invalid module: missing 'name'")

            module.setdefault("format_module", "{output}")
            module.setdefault("interval", None)

            if (
                interval is not None
                and module["interval"] is not None
                and module["interval"] < interval
            ):
                raise Exception(
                    f"'{module['name']}' (interval={module['interval']}) "
                    f"cannot be lower than i3status (interval={interval})"
                )

        self._write_i3status_config()
        self.i3status_command = ["i3status", "-c", self.tmpfile_name]
        self.error = None
        self.process = None
        self.running = True
        self.items = []
        self.line = ""

        self.runtime = {"cache": {}, "name": {"disk_info": "disk"}}
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
        self.general.update({"output_format": "i3bar"})
        lines.append("general {\n")
        for k, v in self.general.items():
            lines.append(f"    {k} = {_format(v)}\n")
        lines.append("}\n\n")
        for module in self.modules:
            lines.append(f'order += "{module["name"]}"\n')
            settings = {
                k: v for k, v in module.items() if k not in ("name", "format_module", "interval")
            }
            if not settings:
                continue
            lines.append(f'{module["name"]} {{\n')
            for k, v in settings.items():
                lines.append(f"    {k} = {_format(v)}\n")
            lines.append("}\n\n")
        tmpfile.write("".join(lines))
        tmpfile.flush()
        tmpfile.close()

    def _find_module(self, item):
        key = (
            self.runtime["name"].get(item.get("name"), item.get("name")),
            item.get("instance", ""),
        )
        try:
            return self.runtime["cache"][key]
        except KeyError:
            pass
        runtime_name, runtime_instance = key
        matches = []
        for module in self.modules:
            name, _, instance = module["name"].partition(" ")
            name = self.runtime["name"].get(name, name)
            if name != runtime_name:
                continue
            if instance == runtime_instance:
                runtime = {"key": key, "config": module, "time": 0, "output": None}
                self.runtime["cache"][key] = runtime
                return runtime
            matches.append(module)
        if len(matches) == 1:
            module = matches[0]
            runtime = {"key": key, "config": module, "time": 0, "output": None}
            self.runtime["cache"][key] = runtime
            return runtime

        module_name = " ".join(filter(None, key))
        message = f"unable to match module '{module_name}'"
        self._set_error(message)
        return None

    def _format_modules(self):
        now = monotonic()
        new_modules = []

        for item in self.items:
            if not item.get("full_text"):
                continue
            runtime = self._find_module(item)
            if not runtime:
                continue

            module = runtime["config"]
            interval = module["interval"]

            if runtime["output"] is None or interval is None or now - runtime["time"] >= interval:
                item = item.copy()
                item.pop("name")
                item.pop("instance", None)

                output = self.py3.safe_format(module["format_module"], {"output": item})
                runtime["output"] = output
                runtime["time"] = now

                if interval:
                    module_name = " ".join(filter(None, runtime["key"]))
                    message = f"refreshing '{module_name}' (interval={interval})"
                    self.py3.log(message)

            new_modules.append(runtime["output"])

        return new_modules

    def _set_error(self, error):
        error = str(error).strip().removeprefix("i3status").strip(" .:")
        if not error:
            error = "stopped unexpectedly"
        self.error = error
        self.py3.log(self.error, self.py3.LOG_ERROR)

    def _cleanup(self):
        self.running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()
            with suppress(FileNotFoundError):
                Path(self.tmpfile_name).unlink()
        self.py3.update()

    def _start_loop(self):
        try:
            self.process = Popen(
                self.i3status_command,
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            while self.running:
                line = self.process.stdout.readline()
                # check eof before stripping so i3bar protocol
                # lines do not look like process exit
                if not line:
                    with suppress(TimeoutExpired):
                        self.process.wait(timeout=0.1)
                    if self.running:
                        self._set_error(self.line)
                    break
                # i3status emits i3bar JSON updates
                # with ',' after the opening '['
                line = line.strip("\n,")
                if line in ["", "[", "]"]:
                    continue
                try:
                    items = json.loads(line)
                except ValueError:
                    self.line = line
                    continue
                if not isinstance(items, list):
                    continue
                self.line = ""
                # refresh when i3status changed data
                if self.items != items:
                    self.items = items
                    self.py3.update()
        except Exception as err:
            if self.running:
                self._set_error(err)
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

    config = {
        "modules": [
            {"name": "ipv6", "format_up": "IPv6 %ip", "format_down": ""},
            {"name": "wireless _first_", "format_up": "WIFI %ip", "format_down": ""},
            {"name": "ethernet _first_", "format_up": "ETH %ip", "format_down": ""},
            {"name": "disk /", "format": "USED_DISK %used"},
            {"name": "memory", "format": "USED_MEM %used"},
            {"name": "load", "format": "LOAD %1min"},
            {"name": "tztime local", "format": "TIME %T"},
            {"name": "cpu_temperature 0", "format": "CPU_TEMP %degrees°C"},
        ],
        "format_module_separator": r"\?color=#666&show \|",
    }
    module_test(Py3status, config=config)
