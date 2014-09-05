# -*- coding: utf8 -*-

from __future__ import division  # python2 compatibility
from time import time, sleep
from subprocess import check_output


"""
Module for displaying vnstat's statistics.
REQUIRE external program called "vnstat" installed and configured to work.

@author shadowprince
@license Eclipse Public License
"""

CACHED_TIME = 3*60  # update time (in seconds)
POSITION = 0  # bar position
STATISTICS_TYPE = "d"  # d for daily, m for monthly

"""
Coloring rules.

If value is bigger that dict key, status string will turn to color, specified in the value.
Example:
COLORING = {
    800: "#dddd00",
    900: "#dd0000",
}
(0 - 800: white, 800-900: yellow, >900 - red)
"""
COLORING = {}

"""
Format of status string.

Placeholders:
    total - total
    up - upload
    down - download
"""
FORMAT = "{total}"

PRECISION = 1  # amount of numbers after dot
MULTIPLIER_TOP = 1024  # if value is greater, divide it with UNIT_MULTI and get next unit from UNITS
LEFT_ALIGN = 0

"""
Format of total, up and down placeholders under FORMAT.
As default, substitutes LEFT_ALIGN and PRECISION as %s and %s
Placeholders:
    value - value (float)
    unit - unit (string)

"""
VALUE_FORMAT = "{value:%s.%sf} {unit}" % (LEFT_ALIGN, PRECISION)

INITIAL_MULTI = 1024  # initial multiplier, if you want to get rid of first bytes, set to 1 to disable
UNIT_MULTI = 1024  # value to divide if rate is greater than MULTIPLIER_TOP
UNITS = ["kb", "mb", "gb", "tb", ]  # list of units, first one - value/INITIAL_MULTI, second - value/1024, third - value/1024^2, etc...


def get_stat():
    """
    Get statistics from devfile in list of lists of words
    """
    def filter_stat():
        for x in check_output(["vnstat", "--dumpdb"]).decode("utf-8").splitlines():
            if x.startswith("{};0;".format(STATISTICS_TYPE)):
                return x

    try:
        type, number, ts, rxm, txm, rxk, txk, fill = filter_stat().split(";")
    except OSError as e:
        print("Looks like you have'nt installed or configured vnstat!")
        raise e
    except ValueError:
        raise RuntimeError("vnstat returned wrong output, maybe it's configured wrong or module is outdated")

    up = (int(txm) * 1024 + int(txk)) * 1024
    down = (int(rxm) * 1024 + int(rxk)) * 1024

    return {"up": up,
            "down": down,
            "total": up+down, }


def divide_and_format(value):
    """
    Divide a value and return formatted string
    """
    value /= INITIAL_MULTI
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

    def currentSpeed(self, json, i3status_config):
        stat = get_stat()

        color = None
        keys = list(COLORING.keys())
        keys.sort()
        for k in keys:
            if stat["total"] < k * 1024 * 1024:
                break
            else:
                color = COLORING[k]

        response = {
            'transformed': True,
            'full_text': FORMAT.format(
                total=divide_and_format(stat['total']),
                up=divide_and_format(stat['up']),
                down=divide_and_format(stat['down']),),
            'name': 'vnstat',
            'cached_until': time() + CACHED_TIME,
        }

        if color:
            response["color"] = color

        return POSITION, response

if __name__ == "__main__":
    x = Py3status()
    while True:
        print(x.currentSpeed(1, 1))
        sleep(1)
