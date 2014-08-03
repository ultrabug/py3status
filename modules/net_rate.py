# -*- coding: utf8 -*-

from __future__ import division  # python2 compatibility
from time import time, sleep


"""
Module for displaying current network transfer rate.

@author shadowprince
@license Eclipse Public License
"""

CACHED_TIME = 1  # update time (in seconds)
POSITION = 1  # bar position

DEVFILE = "/proc/net/dev"  # location of dev file under /proc

INTERFACES = []  # list of interfaces to track
ALL_INTERFACES = True  # ignore INTERFACES, but not INTERFACES_BLACKLIST
INTERFACES_BLACKLIST = ["lo"]  # list of interfaces to ignore

"""
Format of status string.

Placeholders:
    interface - name of interface
    total - total rate
    up - upload rate
    down - download rate
"""
FORMAT = "{interface}: {total}"

"""
Format of total, up and down placeholders under FORMAT.
Placeholders:
    value - value (float)
    unit - unit (string)

"""
VALUE_FORMAT = "{value:0.1f} {unit}"

MULTIPLIER_TOP = 1024  # if value is greater, divide it with UNIT_MULTI and get next unit from UNITS

INITIAL_MULTI = 1024  # initial multiplier, if you want to get rid of first bytes, set to 1 to disable
UNIT_MULTI = 1024  # value to divide if rate is greater than MULTIPLIER_TOP
UNITS = ["kb/s", "mb/s", "gb/s"]  # list of units, first one - value/INITIAL_MULTI, second - value/1024, third - value/1024^2, etc...

NO_CONNECTION = "! no data"  # when there is no data transmitted from the start of the plugin
HIDE_IF_NO = False  # hide indicator if rate == 0


"""
Get statistics from devfile in list of lists of words
"""
def get_stat():
    def dev_filter(x):
        # get first word and remove trailing interface number
        x = x.strip().split(" ")[0][:-1]

        if x in INTERFACES_BLACKLIST:
            return False

        if ALL_INTERFACES:
            return True

        if x in INTERFACES:
            return True

        return False

    # read devfile, skip two header files
    x = filter(dev_filter, open(DEVFILE).readlines()[2:])

    try:
        # split info into words, filter empty ones
        return [list(filter(lambda x: x, _x.split(" "))) for _x in x]

    except StopIteration:
        return None


"""
Divide a value and return formatted string
"""
def divide_and_format(value):
    for i, unit in enumerate(UNITS):
        if value > MULTIPLIER_TOP:
            value /= UNIT_MULTI
        else:
            break

    return VALUE_FORMAT.format(value=value, unit=unit)


class Py3status:
    def __init__(self, *args, **kwargs):
        self.last_stat = get_stat()
        self.last_time = time()
        self.last_interface = None

        super(Py3status).__init__(*args, **kwargs)

    def currentSpeed(self, json, i3status_config):
        ns = get_stat()
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
            self.last_stat = get_stat()
            self.last_time = time()

            # get the interface with max rate
            interface = max(deltas, key=lambda x: deltas[x]['total'])

            # if there is no rate - show last active interface, or hide
            if deltas[interface]['total'] == 0:
                interface = self.last_interface
                hide = HIDE_IF_NO
            # if there is - update last_interface
            else:
                self.last_interface = interface
                hide = False

            # get the deltas into variable
            delta = deltas[interface] if interface else None

        except TypeError:
            delta = None
            interface = None
            hide = HIDE_IF_NO

        return (POSITION, {
                'transformed': True,
                'full_text': "" if hide else
                FORMAT.format(
                    total=divide_and_format(delta['total']),
                    up=divide_and_format(delta['up']),
                    down=divide_and_format(delta['down']),
                    interface=interface[:-1],
                ) if interface else NO_CONNECTION,
                'name': 'speed',
                'cached_until': time() + CACHED_TIME,
                })

if __name__ == "__main__":
    x = Py3status()
    while True:
        print(x.currentSpeed(1, 1))
        sleep(1)
