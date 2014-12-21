# -*- coding: utf8 -*-
"""
Module for displaying information about battery.

Requires:
    - the 'acpi' command line

@author shadowprince
@license Eclipse Public License
"""

from __future__ import division  # python2 compatibility
from time import time

import math
import re
import subprocess

BLOCKS = ["_", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
CHARGING_CHARACTER = "⚡"


class Py3status:
    """
    Configuration parameters:
        - color_* : None means - get it from i3status config
        - format : text with "text" mode. percentage with % replaces {}
        - hide_when_full : hide any information when battery is fully charged
        - mode : for primitive-one-char bar, or "text" for text percentage ouput
    """

    # available configuration parameters
    cache_timeout = 30
    color_bad = None
    color_charging = "#FCE94F"
    color_degraded = None
    color_good = None
    format = "Battery: {}"
    hide_when_full = False
    mode = "bar"

    def battery_level(self, i3s_output_list, i3s_config):
        response = {}

        acpi = subprocess.check_output(["acpi"]).decode('utf-8')
        proc = int(re.search(r"(\d+)%", acpi).group(1))

        charging = bool(re.match(r".*Charging.*", acpi))
        full = bool(
            re.match(r".*Unknown.*", acpi)
            ) or bool(
            re.match(r".*Full.*", acpi)
            )

        if self.mode == "bar":
            character = BLOCKS[int(math.ceil(proc/100*(len(BLOCKS) - 1)))]
        else:
            character = self.format.format(str(proc) + "%")

        if proc < 30:
            response['color'] = (
                self.color_degraded
                if self.color_degraded
                else i3s_config['color_degraded']
            )
        if proc < 10:
            response['color'] = (
                self.color_bad
                if self.color_bad
                else i3s_config['color_bad']
            )

        if full:
            response['color'] = (
                self.color_good
                if self.color_good
                else i3s_config['color_good']
            )
            response['full_text'] = "" if self.hide_when_full else BLOCKS[-1]
        elif charging:
            response['color'] = self.color_charging
            response['full_text'] = CHARGING_CHARACTER
        else:
            response['full_text'] = character

        response['cached_until'] = time() + self.cache_timeout

        return response
