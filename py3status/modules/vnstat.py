# -*- coding: utf-8 -*-
"""
Display vnstat statistics.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 180)
    format: display format for this module (default '{total}')
    initial_multi: set to 1 to disable first bytes
        (default 1024)
    left_align: (default 0)
    multiplier_top: if value is greater, divide it with unit_multi and get
        next unit from units (default 1024)
    precision: (default 1)
    statistics_type: d for daily, m for monthly (default 'd')
    thresholds: thresholds to use for color changes (default [])
    unit_multi: value to divide if rate is greater than multiplier_top
        (default 1024)

Format placeholders:
    {down} download
    {total} total
    {up} upload

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    vnstat: a console-based network traffic monitor

Examples:
```
# colorize thresholds
vnstat {
    format = '[\?color=total {total}]'
    thresholds = [
        (838860800, "degraded"),  # 838860800 B -> 800 MiB
        (943718400, "bad"),       # 943718400 B -> 900 MiB
    ]
}
```

@author shadowprince
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': '826.4 mb'}
"""

from __future__ import division  # python2 compatibility

STRING_NOT_INSTALLED = "not installed"
STRING_INVALID_TYPE = "invalid statistics_type"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 180
    format = "{total}"
    initial_multi = 1024
    left_align = 0
    multiplier_top = 1024
    precision = 1
    statistics_type = "d"
    thresholds = []
    unit_multi = 1024

    def post_config_hook(self):
        """
        Format of total, up and down placeholders under FORMAT.
        As default, substitutes left_align and precision as %s and %s
        Placeholders:
            value - value (float)
            unit - unit (string)
        """
        if not self.py3.check_commands("vnstat"):
            raise Exception(STRING_NOT_INSTALLED)
        elif self.statistics_type not in ["d", "m"]:
            raise Exception(STRING_INVALID_TYPE)
        self.slice = slice(*(3, 6) if self.statistics_type == "d" else (8, 11))
        self.value_format = "{value:%s.%sf} {unit}" % (self.left_align, self.precision)
        # list of units, first one - value/initial_multi, second - value/1024,
        # third - value/1024^2, etc...
        self.units = ["kb", "mb", "gb", "tb"]

        # deprecations
        self.coloring = getattr(self, "coloring", None)
        if self.coloring and not self.thresholds:
            self.thresholds = [
                (num * 1024 ** 2, col) for num, col in self.coloring.items()
            ]

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def _divide_and_format(self, value):
        # Divide a value and return formatted string
        value /= self.initial_multi
        for i, unit in enumerate(self.units):
            if value > self.multiplier_top:
                value /= self.unit_multi
            else:
                break
        return self.value_format.format(value=value, unit=unit)

    def vnstat(self):
        vnstat_data = self.py3.command_output("vnstat --oneline b")
        values = vnstat_data.splitlines()[0].split(";")[self.slice]
        stat = dict(zip(["down", "up", "total"], map(int, values)))
        response = {"cached_until": self.py3.time_in(self.cache_timeout)}

        if self.coloring:
            response["color"] = self.py3.threshold_get_color(stat["total"])

        for x in self.thresholds_init:
            if x in stat:
                self.py3.threshold_get_color(stat[x], x)

        response["full_text"] = self.py3.safe_format(
            self.format,
            dict(
                total=self._divide_and_format(stat["total"]),
                up=self._divide_and_format(stat["up"]),
                down=self._divide_and_format(stat["down"]),
            ),
        )
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
