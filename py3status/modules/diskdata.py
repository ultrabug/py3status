# -*- coding: utf-8 -*-
"""
Display the current disk status.

Configuration parameters:
    disk: disk whose stat to check. Set to 'all' to get global stats.
    precision: amount of numbers after dot
    threshold_fast: threshold above which the data transfer is considered fast
    threshold_slow: threshold below which the data transfer is considered slow

Format placeholders:
    {disk} the selected disk
    {free} free space on disk in GB
    {used} used space on disk in GB
    {used_percent} used space on disk in %
    {read} reading rate
    {total} total IO rate
    {write} writing rate

Color conditionals:
    {free} Change color based on the value of free
    {used} Change color based on the value of used_percent
    {read} Change color based on the value of read
    {total} Change color based on the value of total
    {write} Change color based on the value of write

@author shadowprince
@license Eclipse Public License
"""

from __future__ import division  # python2 compatibility
from time import time
import subprocess

# initial multiplier, if you want to get rid of first bytes, set to 1 to
# disable
INITIAL_MULTI = 1024
# if value is greater, divide it with UNIT_MULTI and get next unit from UNITS
MULTIPLIER_TOP = 999
# value to divide if rate is greater than MULTIPLIER_TOP
UNIT_MULTI = 1024
# list of units, first one - value/INITIAL_MULTI, second - value/1024, third -
# value/1024^2, etc...
UNITS = ["kb/s", "mb/s", "gb/s", "tb/s", ]

SECTOR_SIZE = 512

class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    disk = None
    format = "{disk}: {used_percent}% ({total})"
    precision = 1
    threshold_bad = 10
    threshold_degraded = 100
    threshold_fast = 1024
    threshold_slow = 1

    def __init__(self, *args, **kwargs):
        """
        Format of total, up and down placeholders under self.format.
        As default, substitutes self.left_align and self.precision as %s and %s
        Placeholders:
            value - value (float)
            unit - unit (string)
        """
        self.last_interface = None
        self.last_stat = self._get_io_stats(self.disk)
        self.last_time = time()

    def currentSpeed(self):
        # == 6 characters (from MULTIPLIER_TOP + dot + self.precision)
        if self.precision > 0:
            self.left_align = len(str(MULTIPLIER_TOP)) + 1 + self.precision
        else:
            self.left_align = len(str(MULTIPLIER_TOP))
        self.value_format = "{value:%s.%sf} {unit}" % (
            self.left_align, self.precision
        )

        self.values = {'disk': self.disk}

        if '{read}' in self.format or '{write}' in self.format or '{total}' in self.format:
            # time from previous check
            ios = self._get_io_stats(self.disk)
            timedelta = time() - self.last_time

            read = ios[0] - self.last_stat[0]
            write = ios[1] - self.last_stat[1]

            # update last_ info
            self.last_stat = self._get_io_stats(self.disk)
            self.last_time = time()

            read /= timedelta * INITIAL_MULTI
            write /= timedelta * INITIAL_MULTI

            total = read + write

            self.values['read'] = self._divide_and_format(read)
            self.values['total'] = self._divide_and_format(total)
            self.values['write'] = self._divide_and_format(write)

            if read > self.threshold_fast:
                self.py3.COLOR_READ = self.py3.COLOR_BAD
            elif read > self.threshold_slow:
                self.py3.COLOR_READ = self.py3.COLOR_DEGRADED
            else:
                self.py3.COLOR_READ = self.py3.COLOR_GOOD

            if total > self.threshold_fast:
                self.py3.COLOR_TOTAL = self.py3.COLOR_BAD
            elif total > self.threshold_slow:
                self.py3.COLOR_TOTAL = self.py3.COLOR_DEGRADED
            else:
                self.py3.COLOR_TOTAL = self.py3.COLOR_GOOD

            if write > self.threshold_fast:
                self.py3.COLOR_WRITE = self.py3.COLOR_BAD
            elif write > self.threshold_slow:
                self.py3.COLOR_WRITE = self.py3.COLOR_DEGRADED
            else:
                self.py3.COLOR_WRITE = self.py3.COLOR_GOOD

        if '{free}' in self.format or '{used' in self.format:
            free, used, used_percent = self._get_free_space(self.disk)

            if free < self.threshold_bad:
                self.py3.COLOR_FREE = self.py3.COLOR_BAD
            elif free < self.threshold_degraded:
                self.py3.COLOR_FREE = self.py3.COLOR_DEGRADED
            else:
                self.py3.COLOR_FREE = self.py3.COLOR_GOOD

            if used_percent == 'err':
                self.py3.COLOR_USED = self.py3.COLOR_BAD
            elif used_percent > self.threshold_bad:
                self.py3.COLOR_USED = self.py3.COLOR_BAD
            elif used_percent > self.threshold_degraded:
                self.py3.COLOR_USED = self.py3.COLOR_DEGRADED
            else:
                self.py3.COLOR_USED = self.py3.COLOR_GOOD

            self.values['free'] = '{{:.{}f}}'.format(self.precision).format(free)
            self.values['used'] = '{{:.{}f}}'.format(self.precision).format(used)
            self.values['used_percent'] = '{{:.{}f}}'.format(self.precision).format(used_percent)

        return {'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format, self.values)}

    def _get_free_space(self, disk):
        if not disk:
            disk = '/'
        elif not disk.startswith('/dev/'):
            disk = '/dev/' + disk

        total = 0
        used = 0
        free = 0

        df = subprocess.check_output(['df']).decode('utf-8')
        for line in df.split('\n'):
            if line.startswith(disk):
                data = line.split()
                total += int(data[1]) / 1024 / 1024
                used += int(data[2]) / 1024 / 1024
                free += int(data[3]) / 1024 / 1024

        if total == 0:
            return free, used, 'err'

        return free, used, 100 * used / total

    def _get_io_stats(self, disk):
        if disk and disk.startswith('/dev/'):
            disk = disk[5:]
        read = 0
        write = 0
        with open('/proc/diskstats', 'r') as fd:
            for line in fd:
                if disk and disk in line:
                    data = line.split()
                    read += int(data[5]) * SECTOR_SIZE
                    write += int(data[9]) * SECTOR_SIZE
                else:
                    data = line.split()
                    if data[1] == '0':
                        read += int(data[5]) * SECTOR_SIZE
                        write += int(data[9]) * SECTOR_SIZE
        return read, write

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
