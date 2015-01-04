# -*- coding: utf8 -*-
"""
Module for displaying information about battery.

Requires:
    - the 'acpi' command line

@author shadowprince and AdamBSteele
@license Eclipse Public License
"""

from __future__ import division  # python2 compatibility
from time import time

import math
import subprocess

BLOCKS = ["_", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
CHARGING_CHARACTER = "⚡"
EMPTY_BLOCK_CHARGING = '|'
EMPTY_BLOCK_DISCHARGING = '⍀'
FULL_BLOCK = '█'


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
    notification = False

    def battery_level(self, i3s_output_list, i3s_config):
        response = {}

        #  Example acpi raw output:  "Battery 0: Discharging, 43%, 00:59:20 remaining"
        acpi_raw = subprocess.check_output(["acpi"], stderr=subprocess.STDOUT)
        acpi_clean = acpi_raw.translate(None, ',')

        #  Example list: ['Battery', '0:', 'Discharging', '43%', '00:59:20', 'remaining']
        acpi_list = acpi_clean.split(' ')

        charging = True if acpi_list[2] == "Charging" else False
        percent_charged = int(acpi_list[3].translate(None, '%'))

        self.time_remaining = ' '.join(acpi_list[4:])
        battery_full = False

        if self.mode == "bar":
            if charging:
                full_text = CHARGING_CHARACTER
            else:
                full_text = BLOCKS[int(math.ceil(percent_charged/100*(len(BLOCKS) - 1)))]
        elif self.mode == "ascii_bar":
            full_part = FULL_BLOCK * int(percent_charged/10)
            if charging:
                empty_part = EMPTY_BLOCK_CHARGING * (10 - int(percent_charged/10))
            else:
                empty_part = EMPTY_BLOCK_DISCHARGING * (10 - int(percent_charged/10))
            full_text = full_part + empty_part
        else:
            full_text = self.format.format(str(percent_charged) + "%")

        response['full_text'] = full_text

        if percent_charged < 30:
            response['color'] = (
                self.color_degraded
                if self.color_degraded
                else i3s_config['color_degraded']
            )
        if percent_charged < 10:
            response['color'] = (
                self.color_bad
                if self.color_bad
                else i3s_config['color_bad']
            )

        if battery_full:
            response['color'] = (
                self.color_good
                if self.color_good
                else i3s_config['color_good']
            )
            response['full_text'] = "" if self.hide_when_full else BLOCKS[-1]
        elif charging:
            response['color'] = self.color_charging

        response['cached_until'] = time() + self.cache_timeout

        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Display a notification with the remaining charge time.
        """
        if self.notification and self.time_remaining:
            subprocess.call(
                ['notify-send', '{}'.format(self.time_remaining), '-t', '4000'],
                stdout=open('/dev/null', 'w'),
                stderr=open('/dev/null', 'w')
            )
