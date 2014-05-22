import subprocess
import time
import re
import math

"""
Module for displaying information about battery.

@author shadowprince
@version 1.0
@license Eclipse Public License
"""

CACHE_TIME = 30 # time to update battery
HIDE_WHEN_FULL = True # hide any information when battery is fully charged

MODE = "bar" # for primitive-one-char bar, or "text" for text percentage ouput

BLOCKS = [ "_", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", ] # block for bar
TEXT_FORMAT = "Battery: {}" # text with "text" mode. percentage with % replaces {}

CHARGING_CHARACTER = "⚡" 

# None means - get it from i3 config
COLOR_DEGRADED = None
COLOR_BAD = None
COLOR_CHARGING = "#FCE94F"

class Py3status:
    def currentBattery(self, i3status_output_json, i3status_config):
        response = {'name': 'current-battery-level'}

        acpi = subprocess.check_output(["acpi"]).decode('utf-8')
        proc = int(re.search(r"(\d+)%", acpi).group(1))

        charging = bool(re.match(r".*Charging.*", acpi))
        full = bool(re.match(r".*Unknown.*", acpi)) or bool(re.match(r".*Full.*", acpi))

        if MODE == "bar":
            character = BLOCKS[math.ceil(proc/100*(len(BLOCKS) - 1))]
        else:
            character = TEXT_FORMAT.format(str(proc) + "%")
        
        if proc < 30:
            response['color'] = COLOR_DEGRADED if COLOR_DEGRADED else i3status_config["color_degraded"]
        if proc < 10:
            response['color'] = COLOR_BAD if COLOR_BAD else i3status_config["color_bad"]

        if full:
            response['full_text'] = "" if HIDE_WHEN_FULL else BLOCKS[-1]
        elif charging:
            response['full_text'] = CHARGING_CHAR
            response['color'] = COLOR_CHARGING
        else:
            response['full_text'] = character

        response['cached_until'] = time.time() + CACHE_TIME

        return (0, response)
