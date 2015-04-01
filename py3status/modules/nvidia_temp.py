#!/usr/bin/env python
# encoding: utf-8

"""
Module for displaying NVIDIA GPU temperature

Requires:
    - nvidia-smi

@author jmdana <https://github.com/jmdana>
@license GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>
"""

import re
import shlex
from subprocess import check_output
from time import time

TEMP_RE = re.compile(r"Current Temp\s+:\s+([0-9]+)")

class Py3status:
    # configuration parameters
    cache_timeout = 10
    color_good = None
    color_bad = None
    format_prefix = "GPU: "
    format_units = "°C"
    separator = '|'

    def nvidia_temp(self, i3s_output_list, i3s_config):
        # The whole command:
        # nvidia-smi -q -d TEMPERATURE | sed -nr 's/.*Current Temp.*:[[:space:]]*([0-9]+).*/\1/p'

        out = check_output(shlex.split("nvidia-smi -q -d TEMPERATURE"))
        temps = re.findall(TEMP_RE, out.decode("utf-8"))

        if temps != []:
            data = []
            for temp in temps:
                fmt_str = "{temp}{format_units}".format(
                    temp=temp,
                    format_units=self.format_units
                )
                data.append(fmt_str)

            output = "{format_prefix}{data}".format(
                format_prefix=self.format_prefix,
                data=self.separator.join(data)
            )

            color = self.color_good or i3s_config['color_good']
        else:
            output = "{format_prefix}OFF".format(
                format_prefix=self.format_prefix
            )

            color = self.color_bad or i3s_config['color_bad']

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': output,
            'color': color,
        }

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        "color_good": "#00FF00",
        "color_bad": "#FF0000",
        }

    while True:
        print(x.nvidia_temp([], config))
        sleep(1)
