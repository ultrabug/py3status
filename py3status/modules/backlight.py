# -*- coding: utf-8 -*-
"""
Display the current screen backlight level.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (10s default)
    format: prefix text for the backlight status
    command: the command used to retrieve the bakglight level. 
             By default we use `light` https://github.com/haikarainen/light

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD
"""

import shlex
import subprocess
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '☼: {level}'
    command = "light -G"

    def backlight(self, i3s_output_list, i3s_config):
        brightness = subprocess.check_output(
            shlex.split(self.command)).decode('utf-8').rstrip()
        full_text = self.format.format(level=brightness)
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': full_text,
            'color': '#FFFFFF'
        }
        return response


if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    while True:
        print(x.backlight([], None))
        sleep(1)

