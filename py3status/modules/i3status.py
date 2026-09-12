r"""
Run i3status modules in a shared container.

Configuration parameters:
    format: display format for this module (default '{format_module}')
    format_module_separator: show separator if more than one;
        booleans control native separators (default True)
    general: nested section for general settings (default {})

Format placeholders:
    {format_module} format for i3status modules

Proxy sections:
    <proxy_module>: nested section for module settings
    cache_timeout: refresh interval for this proxy module, otherwise
        the container's own general interval (default None)
    format_module: display format for this proxy module (default '{output}')

format_module placeholders:
    {output} the i3status module's output

Examples:
```
# See `man i3status` for a full list of i3status configuration options.
# Not all of i3status configuration options will be supported or usable.
order += "i3status"
i3status {
    general {
        interval = 5
        colors = True
    }
    format = "I3STATUS {format_module}"
    format_module_separator = "\?color=darkorange \|"

    ipv6 {
        format_up = "%ip"
        format_down = ""
        format_module = "\?if=output [\?color=darkgrey&show IPv6] {output}"
    }
    wireless _first_ {
        format_up = "%quality at %essid, %ip"
        format_down = ""
        format_quality = "%d%s"
        format_module = "\?if=output [\?color=darkgrey&show Wireless] {output}"
        # cache_timeout = 10
    }
    ethernet _first_ {
        format_up = "%ip"
        format_down = ""
        format_module = "\?if=output [\?color=darkgrey&show Ethernet] {output}"
    }
    battery all {
        format = "%status"
        format_down = ""
        status_bat = ""
        format_module = "\?if=output [\?color=darkgrey&show Battery] {output}"
    }
    disk "/" {
        format = "%avail"
        format_module = "[\?color=darkgrey&show Disk] {output}"
    }
    load {
        format = "%1min"
        format_module = "[\?color=darkgrey&show Load] {output}"
    }
    memory {
        format = "%percentage_used"
        format_module = "[\?color=darkgrey&show Memory] {output}"
    }
    tztime local {
        format = "%Y-%m-%d %H:%M:%S"
        format_module = "[\?color=darkgrey&show Time] {output}"
        # cache_timeout = 10
    }
    cpu_temperature 0 {
        format = "%degrees°C"
        format_module = "[\?color=darkgrey&show CPU Temp] {output}"
    }
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
[
    {'full_text': '1.2 TiB'},
    {'full_text': ' | ', 'color': '#666'},
    {'full_text': '2026-01-02 07:40:51 CST'},
]
"""

import json
from contextlib import suppress
from pathlib import Path
from signal import SIG_IGN, SIGCONT, SIGSTOP, SIGTSTP, SIGUSR1
from signal import signal as set_signal_handler
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired
from tempfile import NamedTemporaryFile
from threading import Thread
from time import monotonic, sleep

from py3status.formatter import expand_color
from py3status.i3status import registry

# i3status only accepts strict #rrggbb here - named colors ("lime", "good",
# ...) must be resolved to hex first, confirmed against the real binary.
I3S_COLOR_KEYS = ("color_good", "color_bad", "color_degraded", "color_separator")

# like systemd's StartLimitIntervalSec/Burst: a start only counts against
# the container if it falls within RESPAWN_INTERVAL of the ATTEMPTS-th
# most recent one, so spread-out rare crashes never accumulate - a
# genuine crash loop still exhausts the burst and gives up for good.
RESPAWN_ATTEMPTS = 10
RESPAWN_INTERVAL = 60
RESPAWN_DELAY = 5


def _module_count(count):
    return f"{count} module" if count == 1 else f"{count} modules"


class Py3status:
    """ """

    # available configuration parameters
    format = "{format_module}"
    format_module_separator = True
    general = {}

    class Meta:
        container = True

    def post_config_hook(self):
        # _die() needs this, so it must be set before any check that can call it
        self._module_full_name = self.py3.get_config("module_full_name")
        # deprecated -u/--i3status, honored silently if still passed
        i3status = self.py3.get_config("i3status") or "i3status"
        i3status = self.py3.check_commands(i3status)
        if not i3status:
            self._die("not installed")
            raise Exception("not installed")
        if not self.items:
            # every configured child was non-i3status and got dropped
            self._die("missing bare i3status modules")
            raise Exception("missing bare i3status modules")

        self._render_full_text = (
            self._generated_full_text
            if getattr(self, "_generated", False)
            else self._configured_full_text
        )

        self._write_i3status_config()
        self.i3status_command = [i3status, "-c", self.tmpfile.name]
        self.error = None
        self.process = None
        self.running = True
        self.ready = False
        self.output = []
        self.line = ""
        self.t = Thread(target=self._start_loop)
        self.t.daemon = True
        self.t.start()

    def _write_i3status_config(self):
        def _format(value):
            return json.dumps(value, ensure_ascii=False)

        def _resolve_colors(settings):
            resolved = {}
            for k, v in settings.items():
                if k in I3S_COLOR_KEYS:
                    v = expand_color(v, default=v)
                    if isinstance(v, str) and v.startswith("#") and len(v) > 7:
                        # i3status only accepts strict #rrggbb - it dies
                        # outright on an alpha channel, so drop it
                        v = v[:7]
                resolved[k] = v
            return resolved

        # fmt: off
        prefix = f"py3status-{self._module_full_name.replace(' ', '-')}_"
        try:
            # python 3.12+
            self.tmpfile = NamedTemporaryFile(mode="w", encoding="utf-8", prefix=prefix,
                suffix=".conf", delete=False, delete_on_close=False)
        except TypeError:
            self.tmpfile = NamedTemporaryFile(mode="w", encoding="utf-8", prefix=prefix,
                suffix=".conf", delete=False)
        # fmt: on

        # identify at a glance, eg "# i3status _generated"
        # /tmp/py3status-i3status-_generated_xxxxxxxx.conf
        lines = [f"# {self._module_full_name}\n\n"]
        general = dict(self.general)
        general["output_format"] = "i3bar"
        general = _resolve_colors(general)
        lines.append("general {\n")
        for k, v in general.items():
            lines.append(f"    {k} = {_format(v)}\n")
        lines.append("}\n\n")
        for module in self.items:
            lines.append(f'order += "{module["name"]}"\n')
            settings = {k: v for k, v in module.items() if k != "name" and not k.startswith(".")}
            # always declare the section, even empty - a bare item with no
            # block is invisible to i3status (wireless/ethernet/battery/etc)
            settings = _resolve_colors(settings)
            lines.append(f'{module["name"]} {{\n')
            for k, v in settings.items():
                lines.append(f"    {k} = {_format(v)}\n")
            lines.append("}\n\n")
        self.tmpfile.write("".join(lines).rstrip("\n") + "\n")
        self.tmpfile.close()

    def _start_loop(self):
        # a mid-budget crash leaves the registry alone (proxies keep showing
        # their last output); only the final give-up calls _cleanup().
        starts = []
        while self.running:
            now = monotonic()
            starts = [t for t in starts if now - t < RESPAWN_INTERVAL]
            if len(starts) >= RESPAWN_ATTEMPTS:
                msg = f"giving up: {RESPAWN_ATTEMPTS} restarts within {RESPAWN_INTERVAL}s"
                self.py3.log(msg, self.py3.LOG_WARNING)
                registry.mark_dead(self._module_full_name, msg)
                break
            starts.append(now)
            self._spawn_i3status()
            if not self.ready:
                if self.running:
                    msg = getattr(self, "error", None) or "never started successfully"
                    self.py3.log(f"giving up: {msg}", self.py3.LOG_WARNING)
                    registry.mark_dead(self._module_full_name, msg)
                break
            if not self.running:
                break
            self.py3.log(
                f"restarting (attempt {len(starts)}/{RESPAWN_ATTEMPTS})", self.py3.LOG_WARNING
            )
            sleep(RESPAWN_DELAY)
        self._cleanup()

    def _spawn_i3status(self):
        # blocks reading output lines until the subprocess exits or dies -
        # _start_loop() calls this in a loop, respawning on each return
        try:
            self.process = Popen(
                self.i3status_command,
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                # only our own explicit _suspend() should freeze this -
                # not a stray SIGTSTP hitting the whole process group
                # (eg Ctrl+Z in a terminal)
                preexec_fn=lambda: set_signal_handler(SIGTSTP, SIG_IGN),
            )
            self.py3.log(f"config file: {self.tmpfile.name}")
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
                    # accumulate - an error can span several lines
                    self.line = f"{self.line} {line}".strip()
                    continue
                if not isinstance(items, list):
                    continue
                self.line = ""
                self.ready = True
                if len(items) != len(self.items):
                    # if something emits zero block - positional matching
                    # would misattribute everything after it, so surface it
                    # loudly instead of showing plausible-looking wrong data.
                    msg = (
                        f"expected {_module_count(len(self.items))}, "
                        f"but i3status produced {_module_count(len(items))}"
                    )
                    # same mismatch every tick otherwise - only log a change
                    if msg != getattr(self, "error", None):
                        self._set_error(msg)
                    continue
                self.error = None
                # refresh when i3status changed data
                if self.output != items:
                    first_publish = not self.output
                    self.output = items
                    self._publish_to_registry()
                    if first_publish:
                        # wake proxies immediately instead of leaving
                        # them to find this on their own schedule
                        self._wake_proxies()
                    self.py3.update()
        except Exception as err:
            if self.running:
                self._set_error(err)

    def _publish_to_registry(self):
        # matched positionally, not by name/instance: i3status often
        # substitutes a runtime value (eg "_first_" -> real interface),
        # but always emits output in the same order as our order += lines.
        container_instance = self._module_full_name
        for module, item in zip(self.items, self.output):
            item_name, _, item_instance = module["name"].partition(" ")
            key = (item_name, item_instance or None)
            registry.publish(container_instance, key, item)

    def _set_error(self, error):
        error = str(error).strip()
        # our own tmpfile path/line number are noise, not real context
        error = error.removeprefix(self.tmpfile.name).lstrip(":").strip()
        line_no, _, rest = error.partition(":")
        if line_no.isdigit():
            error = rest.strip()
        before, sep, after = error.partition(", line ")
        if sep:
            error = before + after.lstrip("0123456789")
        error = error.removeprefix("i3status").strip(" .:")
        if not error:
            error = "stopped unexpectedly"
        self.error = error
        self.py3.log(self.error, self.py3.LOG_ERROR)

    def _wake_proxies(self):
        # force each proxy to re-read the registry
        # now, not on its own cache_timeout
        for proxy_name in getattr(self, "_proxies", []):
            self.py3.update(proxy_name)

    def _die(self, reason):
        # post_config_hook() failing skips kill()/_cleanup() entirely, so
        # proxies need an explicit wake here, not just cache_timeout
        registry.mark_dead(self._module_full_name, reason)
        self._wake_proxies()

    def _refresh(self):
        # force a fresh reading right now instead of waiting for the
        # subprocess's own general.interval - see `man i3status` SIGUSR1.
        process = getattr(self, "process", None)
        if process and process.poll() is None:
            process.send_signal(SIGUSR1)

    def _suspend(self):
        # freeze subprocess - eg the bar is hidden/suspended
        process = getattr(self, "process", None)
        if process and process.poll() is None:
            process.send_signal(SIGSTOP)

    def _resume(self):
        # undo _suspend() - eg the bar is visible again
        process = getattr(self, "process", None)
        if process and process.poll() is None:
            process.send_signal(SIGCONT)

    def _cleanup(self):
        # post_config_hook() may have failed before process/tmpfile were
        # ever set at all (not just left None), eg "not installed"
        self.running = False
        process = getattr(self, "process", None)
        if process and process.poll() is None:
            process.terminate()
        tmpfile = getattr(self, "tmpfile", None)
        if tmpfile:
            with suppress(FileNotFoundError):
                Path(tmpfile.name).unlink()
        # container is dead for good - clear its data, then force proxies
        # to reflect that now instead of waiting on their own cache_timeout.
        registry.clear(self._module_full_name)
        self._wake_proxies()
        self.py3.update()

    def _generated_full_text(self):
        # generated containers have no order slot, so this is never displayed
        return ""

    def _configured_full_text(self):
        # has its own order slot - combine its proxies' outputs into a line
        outputs = [self.py3.get_output(name) for name in self._proxies]
        format_module = self.py3.safe_join(self.format_module_separator, outputs)
        return self.py3.safe_format(self.format, {"format_module": format_module})

    def i3status(self):
        if self.error:
            self.py3.error(self.error, self.py3.CACHE_FOREVER)

        return {"cached_until": self.py3.CACHE_FOREVER, "full_text": self._render_full_text()}

    def kill(self):
        self._cleanup()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
