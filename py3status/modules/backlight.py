# -*- coding: utf-8 -*-
"""
Display the current screen backlight level.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default: 10s)
    device: The backlight device (default: "acpi_video0")
            If you are unsure try: `ls /sys/class/backlight`
    color:  The text color (default: "#FFFFFF")

Format status string parameters:
    {level} brightness

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD
"""

from __future__ import division

import subprocess
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    device = "acpi_video0"
    format = u'☼: {level}%'
    color = '#FFFFFF'

    def backlight(self,  i3s_output_list, i3s_config):
        level = int(subprocess.check_output(
            ["cat", "/sys/class/backlight/%s/brightness" % self.device]))
        max_level = int(subprocess.check_output(
            ["cat", "/sys/class/backlight/%s/max_brightness" % self.device]))
        full_text = self.format.format(level=(level * 100 // max_level))
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': full_text,
            'color': self.color
        }
        return response


if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    while True:
        print(x.backlight([], None))
        sleep(1)
