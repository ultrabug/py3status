# -*- coding: utf8 -*-

from __future__ import division  # python2 compatibility
from time import time

import math
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

MODE = "bar"  # for primitive-one-char bar, or "XT


# bar settings
BLOCKS = ["_", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]  # block for bar
TEXT_FORMAT = "Battery: {}"  # text with "text" mode. percentage with % replaces {}
CHARGING_CHARACTER = "⚡"

# ascii_bar settings
FULL_BLOCK = '█'
EMPTY_BLOCK_CHARGING = '|'
EMPTY_BLOCK_DISCHARGING = '⍀'

# None means - get it from i3 config
COLOR_BAD = None
COLOR_CHARGING = "#FCE94F"
COLOR_DEGRADED = None
COLOR_GOOD = None
DISPLAY_TIME_REMAINING = False


class Py3status:

    def battery_level(self, i3status_output_json, i3status_config):
        response = {'name': 'battery-level'}


        #  Example acpi raw output:  "Battery 0: Discharging, 43%, 00:59:20 remaining"
        acpi_raw = subprocess.check_output(["acpi"], stderr=subprocess.STDOUT)

        acpi_clean = acpi_raw.translate(None, ',')        # Remove commas

        #  Example list: ['Battery', '0:', 'Discharging', '43%', '00:59:20', 'remaining']
        acpi_list = acpi_clean.split(' ')

        charging = True if acpi_list[2] == "Charging" else False
        percent_charged = int(acpi_list[3].translate(None, '%'))  #  Remove percent sign

        self.time_remaining = ' '.join(acpi_list[4:])
        battery_full = False


        if MODE == "bar":
            if charging:
                full_text = CHARGING_CHARACTER
            else:
                full_text = BLOCKS[int(math.ceil(percent_charged/100*(len(BLOCKS) - 1)))]

        elif MODE == "ascii_bar":
            full_part = FULL_BLOCK * int(percent_charged/10)
            
            if charging:
                empty_part = EMPTY_BLOCK_CHARGING * (10 - int(percent_charged/10))
            else:
                empty_part = EMPTY_BLOCK_DISCHARGING * (10 - int(percent_charged/10))

            full_text =  full_part + empty_part
        else:
            full_text = TEXT_FORMAT.format(str(percent_charged) + "%")

        response['full_text'] = full_text

        if percent_charged < 30:
            response['color'] = COLOR_DEGRADED if COLOR_DEGRADED else i3status_config['color_degraded']
        if percent_charged < 10:
            response['color'] = COLOR_BAD if COLOR_BAD else i3status_config['color_bad']

        if battery_full:
            response['color'] = COLOR_GOOD if COLOR_GOOD else i3status_config['color_good']
            response['full_text'] = "" if HIDE_WHEN_FULL else BLOCKS[-1]
        elif charging:
            response['color'] = COLOR_CHARGING
        
        return (0, response)
    
    def on_click(self, i3status_output_json, i3status_config, event):
        subprocess.call(['notify-send', self.time_remaining, '-t', '4000'],
                    stdout=open('/dev/null', 'w'),
                    stderr=open('/dev/null', 'w'))
        os.system("killall -USR1 py3status")
