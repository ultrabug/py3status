# -*- coding: utf-8 -*-
"""
Display the I/O activity on all disks
This modules requires the psutil python module.

Configuration parameters:
    format: format status string
        (default: "{total}")
    precision: precision to display
        (default: 1)
    threshold_bad: use color_bad below this
    threshold_degraded: use color_degraded above this and threshold_bad

Format status string parameters:
    {total} total IO on all disks
"""

# import your useful libs here
from time import time
import psutil


# initial multiplier, if you want to get rid of first bytes set to 1 to disable
INITIAL_MULTI = 1024
MULTIPLIER_TOP = 999  # if value is greater, divide it with UNIT_MULTI and get next unit from UNITS
UNIT_MULTI = 1024  # value to divide if rate is greater than MULTIPLIER_TOP
# list of units: first one - value/INITIAL_MULTI, second - value/1024, third - value/1024^2, etc...
UNITS = ["kb/s", "mb/s", "gb/s", "tb/s", ]


class Py3status:
    threshold_degraded = 1024
    threshold_bad = 10240
    format = "{total}"
    precision = 1
    cache_timeout = 1

    def __init__(self):
        self.last_stat = self._get_stat()
        self.last_time = time()

    def disk_io(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': ''
        }

        # == 6 characters (from MULTIPLIER_TOP + dot + self.precision)
        if self.precision > 0:
            self.left_align = len(str(MULTIPLIER_TOP)) + 1 + self.precision
        else:
            self.left_align = len(str(MULTIPLIER_TOP))
        self.value_format = "{value:%s.%sf} {unit}" % (self.left_align, self.precision)

        iostat = self._get_stat()
        t = time()
        io_speed = (iostat - self.last_stat) / (t - self.last_time)
        self.last_stat = iostat
        self.last_time = t

        if io_speed < self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif io_speed < self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        response['full_text'] = self.py3.safe_format(self.format,
                                                     {'total': self._divide_and_format(io_speed)})

        return response

    def _get_stat(self):
        iostat = psutil.disk_io_counters()
        return iostat.read_bytes + iostat.write_bytes

    def _divide_and_format(self, value):
        """
        Divide a value and return formatted string
        """
        for i, unit in enumerate(UNITS):
            if value > MULTIPLIER_TOP:
                value /= UNIT_MULTI
            else:
                break

        return self.value_format.format(value=value, unit=unit)

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
