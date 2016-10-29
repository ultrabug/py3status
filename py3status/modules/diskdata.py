# -*- coding: utf-8 -*-
"""
Display advanced disk usage information

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds.
        (default 10)
    disk: disk whose stat to check. Set to 'all' to get global stats.
        (default None)
    format: format of the output.
        (default "{disk}: {used_percent}% ({total})")
    initial_multi: initial multiplier, if you want to get rid of first bytes, set to 1 to disable
        (default 1024)
    multiplier_top: if value is greater, divide it with `unit_multi` and get next unit from `units`
        (default 999)
    precision: precision to use for values.
        (default 1)
    sector_size: size of the disk's sectors.
        (default 512)
    thresholds: thresholds to use for color changes
        (default {'free': [(0, "bad"), (10, "degraded"), (100, "good")],
        'total': [(0, "good"), (1, "degraded"), (1024, "bad")]})
    unit_multi: value to divide if rate is greater than MULTIPLIER_TOP
        (default 1024)
    units: list of units, for `value/initial_multi`, value/1024, value/1024^2, etc...
        (default ["kb/s", "mb/s", "gb/s", "tb/s"])

Format placeholders:
    {disk} the selected disk
    {free} free space on disk in GB
    {used} used space on disk in GB
    {used_percent} used space on disk in %
    {read} reading rate
    {total} total IO rate
    {write} writing rate

Color thresholds:
    {free} Change color based on the value of free
    {used} Change color based on the value of used_percent
    {read} Change color based on the value of read
    {total} Change color based on the value of total
    {write} Change color based on the value of write

@author guiniol
@license BSD
"""

from __future__ import division  # python2 compatibility
from time import time
import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    disk = None
    format = "{disk}: {used_percent}% ({total})"
    initial_multi = 1024
    multiplier_top = 999
    precision = 1
    sector_size = 512
    thresholds = {
            'free': [(0, "bad"), (10, "degraded"), (100, "good")],
            'total': [(0, "good"), (1, "degraded"), (1024, "bad")]
            }
    unit_multi = 1024
    units = ["kb/s", "mb/s", "gb/s", "tb/s"]

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
        # == 6 characters (from multiplier_top + dot + self.precision)
        if self.precision > 0:
            self.left_align = len(str(self.multiplier_top)) + 1 + self.precision
        else:
            self.left_align = len(str(self.multiplier_top))
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

            read /= timedelta * self.initial_multi
            write /= timedelta * self.initial_multi

            total = read + write

            self.values['read'] = self._divide_and_format(read)
            self.values['total'] = self._divide_and_format(total)
            self.values['write'] = self._divide_and_format(write)
            self.py3.threshold_get_color(read, 'read')
            self.py3.threshold_get_color(total, 'total')
            self.py3.threshold_get_color(write, 'write')

        if '{free}' in self.format or '{used' in self.format:
            free, used, used_percent = self._get_free_space(self.disk)

            self.values['free'] = '{{:.{}f}}'.format(self.precision).format(free)
            self.values['used'] = '{{:.{}f}}'.format(self.precision).format(used)
            self.values['used_percent'] = '{{:.{}f}}'.format(self.precision).format(used_percent)
            self.py3.threshold_get_color(free, 'free')
            self.py3.threshold_get_color(used, 'used')

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
                    read += int(data[5]) * self.sector_size
                    write += int(data[9]) * self.sector_size
                else:
                    data = line.split()
                    if data[1] == '0':
                        read += int(data[5]) * self.sector_size
                        write += int(data[9]) * self.sector_size
        return read, write

    def _divide_and_format(self, value):
        """
        Divide a value and return formatted string
        """
        for i, unit in enumerate(self.units):
            if value > self.multiplier_top:
                value /= self.unit_multi
            else:
                break

        return self.value_format.format(value=value, unit=unit)

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
