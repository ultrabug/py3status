# -*- coding: utf-8 -*-
"""
Display vnstat statistics.

Configuration parameters:
    cache_timeout: (default 180)
    coloring: (default {})
    format: (default '{total}')
    initial_multi: (default 1024)
    left_align: (default 0)
    multiplier_top: (default 1024)
    precision: (default 1)
    statistics_type: (default 'd')
    unit_multi: (default 1024)

Coloring rules.

If value is bigger that dict key, status string will turn to color, specified
in the value.

Example:
        coloring = {
        800: "#dddd00",
        900: "#dd0000",
        }
        (0 - 800: white, 800-900: yellow, >900 - red)

Format placeholders:
    {down} download
    {total} total
    {up} upload

Requires:
    - external program called `vnstat` installed and configured to work.

@author shadowprince
@license Eclipse Public License
"""

from __future__ import division  # python2 compatibility
from time import time
from subprocess import check_output


def get_stat(statistics_type):
    """
    Get statistics from devfile in list of lists of words
    """
    def filter_stat():
        out = check_output(["vnstat", "--dumpdb"]).decode("utf-8").splitlines()
        for x in out:
            if x.startswith("{};0;".format(statistics_type)):
                return x

    try:
        type, number, ts, rxm, txm, rxk, txk, fill = filter_stat().split(";")
    except OSError as e:
        print("Looks like you haven't installed or configured vnstat!")
        raise e
    except ValueError:
        err = "vnstat returned wrong output, "
        err += "maybe it's configured wrong or module is outdated"
        raise RuntimeError(err)

    up = (int(txm) * 1024 + int(txk)) * 1024
    down = (int(rxm) * 1024 + int(rxk)) * 1024

    return {
        "up": up,
        "down": down,
        "total": up+down
    }


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 180
    coloring = {}
    format = "{total}"
    # initial multiplier, if you want to get rid of first bytes, set to 1 to
    # disable
    initial_multi = 1024
    left_align = 0
    # if value is greater, divide it with unit_multi and get next unit from
    # units
    multiplier_top = 1024
    precision = 1
    statistics_type = "d"  # d for daily, m for monthly
    unit_multi = 1024  # value to divide if rate is greater than multiplier_top

    def __init__(self, *args, **kwargs):
        """
        Format of total, up and down placeholders under FORMAT.
        As default, substitutes left_align and precision as %s and %s
        Placeholders:
            value - value (float)
            unit - unit (string)
        """
        self.last_stat = get_stat(self.statistics_type)
        self.last_time = time()
        self.last_interface = None
        self.value_format = "{value:%s.%sf} {unit}" % (
            self.left_align, self.precision
        )
        # list of units, first one - value/initial_multi, second - value/1024,
        # third - value/1024^2, etc...
        self.units = ["kb", "mb", "gb", "tb", ]

    def _divide_and_format(self, value):
        """
        Divide a value and return formatted string
        """
        value /= self.initial_multi
        for i, unit in enumerate(self.units):
            if value > self.multiplier_top:
                value /= self.unit_multi
            else:
                break

        return self.value_format.format(value=value, unit=unit)

    def currentSpeed(self):
        stat = get_stat(self.statistics_type)

        color = None
        keys = list(self.coloring.keys())
        keys.sort()
        for k in keys:
            if stat["total"] < k * 1024 * 1024:
                break
            else:
                color = self.coloring[k]

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format,
                dict(total=self._divide_and_format(stat['total']),
                     up=self._divide_and_format(stat['up']),
                     down=self._divide_and_format(stat['down'])),
            ),
            'transformed': True
        }

        if color:
            response["color"] = color

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
