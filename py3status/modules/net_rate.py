# -*- coding: utf-8 -*-
"""
Display the current network transfer rate.

Configuration parameters:
    all_interfaces: ignore self.interfaces, but not self.interfaces_blacklist
        (default True)
    cache_timeout: how often we refresh this module in seconds (default 2)
    devfile: location of dev file under /proc (default '/proc/net/dev')
    format: format of the module output (default '{interface}: {total}')
    format_no_connection: when there is no data transmitted from the
        start of the plugin (default '')
    hide_if_zero: hide indicator if rate == 0 (default False)
    interfaces: comma separated list of interfaces to track (default '')
    interfaces_blacklist: comma separated list of interfaces to ignore
        (default 'lo')
    precision: amount of numbers after dot (default 1)
    threshold_fast: threshold above which the data transfer is considered fast
    threshold_slow: threshold below which the data transfer is considered slow

Format placeholders:
    {down} download rate
    {interface} name of interface
    {total} total rate
    {up} upload rate

Color conditionals:
    {down} Change color based on the value of down
    {total} Change color based on the value of total
    {up} Change color based on the value of up

@author shadowprince
@license Eclipse Public License
"""

from __future__ import division  # python2 compatibility
from time import time

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


class Py3status:
    """
    """
    # available configuration parameters
    all_interfaces = True
    cache_timeout = 2
    devfile = '/proc/net/dev'
    format = "{interface}: {total}"
    format_no_connection = ''
    hide_if_zero = False
    interfaces = ''
    interfaces_blacklist = 'lo'
    precision = 1
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
        self.last_stat = self._get_stat()
        self.last_time = time()

    def currentSpeed(self):
        # parse some configuration parameters
        if not isinstance(self.interfaces, list):
            self.interfaces = self.interfaces.split(',')
        if not isinstance(self.interfaces_blacklist, list):
            self.interfaces_blacklist = self.interfaces_blacklist.split(',')

        # == 6 characters (from MULTIPLIER_TOP + dot + self.precision)
        if self.precision > 0:
            self.left_align = len(str(MULTIPLIER_TOP)) + 1 + self.precision
        else:
            self.left_align = len(str(MULTIPLIER_TOP))
        self.value_format = "{value:%s.%sf} {unit}" % (
            self.left_align, self.precision
        )

        ns = self._get_stat()
        deltas = {}
        try:
            # time from previous check
            timedelta = time() - self.last_time

            # calculate deltas for all interfaces
            for old, new in zip(self.last_stat, ns):
                down = int(new[1]) - int(old[1])
                up = int(new[9]) - int(old[9])

                down /= timedelta * INITIAL_MULTI
                up /= timedelta * INITIAL_MULTI

                deltas[new[0]] = {'total': up+down, 'up': up, 'down': down, }

            # update last_ info
            self.last_stat = self._get_stat()
            self.last_time = time()

            # get the interface with max rate
            interface = max(deltas, key=lambda x: deltas[x]['total'])

            # if there is no rate - show last active interface, or hide
            if deltas[interface]['total'] == 0:
                interface = self.last_interface
                hide = self.hide_if_zero
            # if there is - update last_interface
            else:
                self.last_interface = interface
                hide = False

            # get the deltas into variable
            delta = deltas[interface] if interface else None

        except TypeError:
            delta = None
            interface = None
            hide = self.hide_if_zero

        if interface:

            if delta['down'] < self.threshold_slow:
                self.py3.COLOR_DOWN = self.py3.COLOR_BAD
            elif delta['down'] < self.threshold_fast:
                self.py3.COLOR_DOWN = self.py3.COLOR_DEGRADED
            else:
                self.py3.COLOR_DOWN = self.py3.COLOR_GOOD

            if delta['total'] < self.threshold_slow:
                self.py3.COLOR_TOTAL = self.py3.COLOR_BAD
            elif delta['total'] < self.threshold_fast:
                self.py3.COLOR_TOTAL = self.py3.COLOR_DEGRADED
            else:
                self.py3.COLOR_TOTAL = self.py3.COLOR_GOOD

            if delta['up'] < self.threshold_slow:
                self.py3.COLOR_UP = self.py3.COLOR_BAD
            elif delta['up'] < self.threshold_fast:
                self.py3.COLOR_UP = self.py3.COLOR_DEGRADED
            else:
                self.py3.COLOR_UP = self.py3.COLOR_GOOD

        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        if hide:
            response['full_text'] = ""
        elif not interface:
            response['full_text'] = self.format_no_connection
        else:
            response['full_text'] = self.py3.safe_format(self.format, {
                'down': self._divide_and_format(delta['down']),
                'total': self._divide_and_format(delta['total']),
                'up': self._divide_and_format(delta['up']),
                'interface': interface[:-1],
                })

        return response

    def _get_stat(self):
        """
        Get statistics from devfile in list of lists of words
        """
        def dev_filter(x):
            # get first word and remove trailing interface number
            x = x.strip().split(" ")[0][:-1]

            if x in self.interfaces_blacklist:
                return False

            if self.all_interfaces:
                return True

            if x in self.interfaces:
                return True

            return False

        # read devfile, skip two header files
        x = filter(dev_filter, open(self.devfile).readlines()[2:])

        try:
            # split info into words, filter empty ones
            return [list(filter(lambda x: x, _x.split(" "))) for _x in x]

        except StopIteration:
            return None

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
