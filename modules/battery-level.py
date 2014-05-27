# -*- coding: utf8 -*-

from __future__ import division  # python2 compatibility
from time import time

import math
import re
import subprocess

"""
Module for displaying information about battery.

Requires:
    - the 'acpi' command line

@author shadowprince
@license Eclipse Public License
"""

CACHE_TIMEOUT = 30  # time to update battery
HIDE_WHEN_FULL = False  # hide any information when battery is fully charged

MODE = "bar"  # for primitive-one-char bar, or "text" for text percentage ouput

BLOCKS = ["_", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]  # block for bar
TEXT_FORMAT = "Battery: {}"  # text with "text" mode. percentage with % replaces {}

CHARGING_CHARACTER = "⚡"

# None means - get it from i3 config
COLOR_BAD = None
COLOR_CHARGING = "#FCE94F"
COLOR_DEGRADED = None
COLOR_GOOD = None


class Py3status:
    def battery_level(self, i3status_output_json, i3status_config):
        response = {'name': 'battery-level'}

        acpi = subprocess.check_output(["acpi"]).decode('utf-8')
        proc = int(re.search(r"(\d+)%", acpi).group(1))

        charging = bool(re.match(r".*Charging.*", acpi))
        full = bool(re.match(r".*Unknown.*", acpi)) or bool(re.match(r".*Full.*", acpi))

        if MODE == "bar":
            character = BLOCKS[int(math.ceil(proc/100*(len(BLOCKS) - 1)))]
        else:
            character = TEXT_FORMAT.format(str(proc) + "%")

        if proc < 30:
            response['color'] = COLOR_DEGRADED if COLOR_DEGRADED else i3status_config['color_degraded']
        if proc < 10:
            response['color'] = COLOR_BAD if COLOR_BAD else i3status_config['color_bad']

        if full:
            response['color'] = COLOR_GOOD if COLOR_GOOD else i3status_config['color_good']
            response['full_text'] = "" if HIDE_WHEN_FULL else BLOCKS[-1]
        elif charging:
            response['color'] = COLOR_CHARGING
            response['full_text'] = CHARGING_CHARACTER
        else:
            response['full_text'] = character

        response['cached_until'] = time() + CACHE_TIMEOUT

        return (0, response)
