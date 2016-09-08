# -*- coding: utf-8 -*-
"""
Display the current screen backlight level.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default: 10s)
    color:         The text color (default: "#FFFFFF")
    device:        The backlight device
                   If not specified the plugin will detect it automatically
    format:        Display brightness, see placeholders below

Format status string parameters:
    {level} brightness

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD
"""

from __future__ import division

import os
from time import time


def get_device_path():
    for (path, devices, files) in os.walk('/sys/class/backlight/'):
        for device in devices:
            if 'brightness' in os.listdir(path + device) and \
               'max_brightness' in os.listdir(path + device):
                return path + device


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    color = '#FFFFFF'
    device_path = None
    format = u'☼: {level}%'
    
    def backlight(self,  i3s_output_list, i3s_config):
        if not self.device_path:
            if not hasattr(self, 'device'):
                self.device_path = get_device_path()
            else:
                self.device_path = "/sys/class/backlight/%s" % self.device

        for brightness_line in open("%s/brightness" % self.device_path, 'rb'):
            brightness = int(brightness_line)
        for brightness_max_line in open("%s/max_brightness" % self.device_path, 'rb'):
            brightness_max = int(brightness_max_line)

        full_text = self.format.format(level=(brightness * 100 // brightness_max))
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
