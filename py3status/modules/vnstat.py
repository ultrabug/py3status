# -*- coding: utf-8 -*-
"""
Display vnstat statistics.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 180)
    coloring: see coloring rules below (default {})
    format: display format for this module (default '{total}')
    initial_multi: set to 1 to disable first bytes
        (default 1024)
    left_align: (default 0)
    multiplier_top: if value is greater, divide it with unit_multi and get
        next unit from units (default 1024)
    precision: (default 1)
    statistics_type: d for daily, m for monthly (default 'd')
    unit_multi: value to divide if rate is greater than multiplier_top
        (default 1024)

Coloring rules:
    If value is more than dict key, the string will change color based on the
    specified values in the coloring section.

Example:
```
    coloring = {
        800: "#dddd00",     # over 800: yellow
        900: "#dd0000",     # over 900: red
    }
```

Format placeholders:
    {down} download
    {total} total
    {up} upload

Requires:
    vnstat: a console-based network traffic monitor

@author shadowprince
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': '826.4 mb'}
"""

from __future__ import division  # python2 compatibility
STRING_NOT_INSTALLED = 'not installed'
STRING_INVALID_TYPE = "invalid statistics_type"


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 180
    coloring = {}
    format = "{total}"
    initial_multi = 1024
    left_align = 0
    multiplier_top = 1024
    precision = 1
    statistics_type = "d"
    unit_multi = 1024

    def post_config_hook(self):
        """
        Format of total, up and down placeholders under FORMAT.
        As default, substitutes left_align and precision as %s and %s
        Placeholders:
            value - value (float)
            unit - unit (string)
        """
        if not self.py3.check_commands('vnstat'):
            raise Exception(STRING_NOT_INSTALLED)
        elif self.statistics_type not in ["d", "m"]:
            raise Exception(STRING_INVALID_TYPE)
        self.slice = slice(*(3, 6) if self.statistics_type == "d" else (8, 11))
        self.value_format = "{value:%s.%sf} {unit}" % (self.left_align, self.precision)
        # list of units, first one - value/initial_multi, second - value/1024,
        # third - value/1024^2, etc...
        self.units = ["kb", "mb", "gb", "tb", ]

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
        values = vnstat_data.splitlines()[0].split(';')[self.slice]
        stat = dict(zip(["down", "up", "total"], map(int, values)))
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        keys = list(self.coloring.keys())
        keys.sort()
        for k in keys:
            if stat["total"] < k * 1024 * 1024:
                break
            else:
                response['color'] = self.coloring[k]

        response['full_text'] = self.py3.safe_format(
            self.format,
            dict(total=self._divide_and_format(stat['total']),
                 up=self._divide_and_format(stat['up']),
                 down=self._divide_and_format(stat['down'])))
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
