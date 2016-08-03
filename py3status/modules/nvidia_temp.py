# -*- coding: utf-8 -*-
"""
Display NVIDIA GPU temperature.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
    color_bad: the color used if the temperature can't be read.
    color_good: the color used if everything is OK.
    format_prefix: a prefix for the output.
    format_units: the temperature units. Will appear at the end.
    temp_separator: the separator char between temperatures (only if more than
        one GPU)

Requires:
    nvidia-smi:

@author jmdana <https://github.com/jmdana>
@license BSD
"""

import re
import shlex
from subprocess import check_output
from time import time

TEMP_RE = re.compile(r"Current Temp\s+:\s+([0-9]+)")


class Py3status:
    """
    """
    # configuration parameters
    cache_timeout = 10
    color_bad = None
    color_good = None
    format_prefix = "GPU: "
    format_units = "°C"
    temp_separator = '|'

    def nvidia_temp(self, i3s_output_list, i3s_config):
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
                data=self.temp_separator.join(data)
            )

            color = self.color_good or i3s_config['color_good']
        else:
            output = "{format_prefix}OFF".format(
                format_prefix=self.format_prefix
            )

            color = self.color_bad or i3s_config['color_bad']

        response = {
            'cached_until': time() + self.cache_timeout,
            'color': color,
            'full_text': output
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
