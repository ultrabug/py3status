"""
Native reimplementation of i3status's `load` module.

Gets the system load (number of processes waiting for CPU time in
the last 1, 5 and 15 minutes).

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: see placeholders below (default '%1min %5min %15min')
    format_above_threshold: format used when the 1-minute load average is at
        or above max_threshold (default None, uses format)
    max_threshold: 1-minute load average at/above which color_bad is used
        (default 5)

Format placeholders:
    %1min the 1 minute load average
    %5min the 5 minute load average
    %15min the 15 minute load average

Color options:
    color_bad: 1-minute load average is at/above max_threshold

Type: Singleton (supports only one, unnamed section)

Notes:
    If getloadavg() fails, outputs "cant read load" with no color,
    matching real i3status exactly.

@author claude
"""

import os

from py3status.i3status.helpers import resolve_cache_timeout


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%1min %5min %15min"
    format_above_threshold = None
    max_threshold = 5

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)

    def load(self):
        try:
            one, five, fifteen = os.getloadavg()
        except OSError:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": "cant read load",
            }

        above_threshold = one >= self.max_threshold
        format_string = self.format
        if above_threshold and self.format_above_threshold is not None:
            format_string = self.format_above_threshold

        full_text = format_string.replace("%1min", f"{one:.2f}")
        full_text = full_text.replace("%5min", f"{five:.2f}")
        full_text = full_text.replace("%15min", f"{fifteen:.2f}")

        response = {"cached_until": self.py3.time_in(self.cache_timeout), "full_text": full_text}
        if above_threshold:
            response["color"] = self.py3.COLOR_BAD
        return response


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
