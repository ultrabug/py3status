"""
Native reimplementation of i3status's `cpu_temperature` module.

Gets the temperature of the given thermal zone.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: see placeholders below (default '%degrees C')
    format_above_threshold: format used when the temperature is at/above
        max_threshold (default None, uses format)
    max_threshold: temperature (degrees C) at/above which color_bad is
        used (default 75)
    path: path or glob pattern to read instead of the default thermal
        zone path; '%d' is replaced by zone if there's no glob match
        (default None)
    zone: thermal zone number (default 0)

Format placeholders:
    %degrees the temperature, in whole degrees C, or '?' if unavailable

Color options:
    color_bad: temperature is at/above max_threshold

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Reads /sys/class/thermal/thermal_zoneN/temp (or a user-provided
    path/glob).

    Real i3status has no 'zone' config key - it comes from the
    section's title instead (eg `cpu_temperature 0 { }` gives zone=0).
    This module exposes 'zone' as an ordinary config key instead, so it
    works with zero config; it's stripped automatically if the section
    resolves to the real i3status wrapper, since real i3status crashes
    on an unrecognized option.

@author claude
"""

from glob import glob

from py3status.i3status.helpers import (
    format_placeholders,
    resolve_cache_timeout,
)

DEFAULT_PATH = "/sys/class/thermal/thermal_zone%d/temp"


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%degrees C"
    format_above_threshold = None
    max_threshold = 75
    path = None
    zone = 0

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        self.py3.log(
            f"cpu_temperature: reading {self._resolve_path(self.path, self.zone)!r}", "debug"
        )

    @staticmethod
    def _resolve_path(path, zone):
        path = path or DEFAULT_PATH
        # sorted() to match glibc's glob(), which sorts by default (the C code
        # doesn't pass GLOB_NOSORT); Python's glob.glob() makes no such guarantee
        matches = sorted(glob(path))
        if matches:
            return matches[0]
        try:
            return path % zone
        except TypeError:
            # no %d-style placeholder in path; use it verbatim
            return path

    @staticmethod
    def _read_temperature(path):
        """Return (raw_degrees_int_or_None, formatted_string)."""
        try:
            with open(path) as f:
                millidegrees = int(f.read().strip())
        except (OSError, ValueError):
            return None, None

        degrees = millidegrees // 1000
        if degrees <= 0:
            return degrees, "?"
        return degrees, str(degrees)

    def cpu_temperature(self):
        path = self._resolve_path(self.path, self.zone)
        degrees, formatted = self._read_temperature(path)

        if degrees is None:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": "can't read temp",
            }

        selected_format = self.format
        color = None
        if degrees >= self.max_threshold:
            color = self.py3.COLOR_BAD
            if self.format_above_threshold is not None:
                selected_format = self.format_above_threshold

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(selected_format, [("%degrees", formatted)]),
        }
        if color:
            response["color"] = color
        return response


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
