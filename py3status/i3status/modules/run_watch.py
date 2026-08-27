"""
Native reimplementation of i3status's `run_watch` module.

Expands the given path to a pidfile and checks if the process ID
found inside is valid (that is, if the process is running). You can
use this to check if a specific application, such as a VPN client or
your DHCP client is running.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: see placeholders below (default '%title: %status')
    format_down: format used when the process isn't running
        (default None, uses format)
    pidfile: path (glob pattern and '~' both expanded) to a file
        containing the watched process's PID (default None)
    title: label available as the %title placeholder (default None)

Format placeholders:
    %title the configured title
    %status 'yes' if the process is running, 'no' otherwise

Color options:
    color_good: process is running
    color_bad: process is not running

Type: Instance (supports multiple sections via an instance/title)

Notes:
    If pidfile is a glob matching several files, they're checked in
    order and the first readable one decides the result - an unreadable
    match means "not running", even if a later match would have
    succeeded (matches i3status, which gives up at the first unreadable
    match).

    Real i3status has no 'title' config key - it comes from the
    section's title instead (eg `run_watch VPN { }` gives title="VPN").
    This module exposes 'title' as an ordinary config key instead, so
    it works with zero config; it's stripped automatically if the
    section resolves to the real i3status wrapper, since real i3status
    crashes on an unrecognized option.

    Both 'title' and 'pidfile' are required - post_config_hook() raises
    if either is unset. Real i3status crashes its whole process instead
    if pidfile is unset while the section is present; this module
    disables just the one module instead.

@author claude
"""

import os
from glob import glob

from py3status.i3status.helpers import format_placeholders, resolve_cache_timeout


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%title: %status"
    format_down = None
    pidfile = None
    title = None

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        missing = [k for k, v in (("title", self.title), ("pidfile", self.pidfile)) if v is None]
        if missing:
            raise Exception(f"missing {', '.join(missing)}")
        self._expanded_pidfile = os.path.expanduser(self.pidfile)

    @staticmethod
    def _process_runs(expanded_pidfile):
        """expanded_pidfile must already have '~' expanded by the caller - that
        part of the path is static config, only the glob itself needs to be
        re-evaluated every tick."""
        # sorted() to match glibc's glob(), which sorts by default (the C code
        # doesn't pass GLOB_NOSORT); Python's glob.glob() makes no such guarantee
        matches = sorted(glob(expanded_pidfile)) or [expanded_pidfile]

        for path in matches:
            try:
                with open(path) as f:
                    pid = int(f.read().strip())
            except (OSError, ValueError):
                return False

            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                continue
            except PermissionError:
                return True
            else:
                return True

        return False

    def run_watch(self):
        running = self._process_runs(self._expanded_pidfile)

        selected_format = self.format if running or self.format_down is None else self.format_down
        placeholders = [("%title", self.title), ("%status", "yes" if running else "no")]

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(selected_format, placeholders),
            "color": self.py3.COLOR_GOOD if running else self.py3.COLOR_BAD,
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
