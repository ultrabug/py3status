# -*- coding: utf-8 -*-
"""
Display NVIDIA GPU temperature.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    format_prefix: a prefix for the output. (default 'GPU: ')
    format_units: the temperature units. Will appear at the end. (default '°C')
    temp_separator: the separator char between temperatures (only if more than
        one GPU) (default '|')

Color options:
    color_bad: Temperature can't be read.
    color_good: Everything is OK.

Requires:
    nvidia-smi:

@author jmdana <https://github.com/jmdana>
@license BSD
"""

import re
import shlex
from subprocess import check_output

TEMP_RE = re.compile(r"Current Temp\s+:\s+([0-9]+)")


class Py3status:
    """
    """
    # configuration parameters
    cache_timeout = 10
    format_prefix = "GPU: "
    format_units = u"°C"
    temp_separator = '|'

    def nvidia_temp(self):
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

            color = self.py3.COLOR_GOOD
        else:
            output = "{format_prefix}OFF".format(
                format_prefix=self.format_prefix
            )

            color = self.py3.COLOR_BAD

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
            'full_text': output
        }

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
