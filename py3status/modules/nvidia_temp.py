# -*- coding: utf-8 -*-
"""
Display NVIDIA GPU temperatures.

Configuration parameters:
    cache_timeout: refresh interval for this module in seconds (default 10)
    format: display format for this module (default 'GPU: {format_temp}')
    format_temp: display format for this placeholder (default '{temp}°C')
    string_separator: display separator (only if more than one) (default '|')
    string_unavailable: display unavailable (default 'nvidia_temp: N/A')

Format placeholders:
    {format_temp} display format for temperatures

format_temp placeholders:
    {temp} current temperature

Color options:
    color_bad: Unavailable
    color_good: Available

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
    format = "GPU: {format_temp}"
    format_temp = u"{temp}°C"
    string_separator = '|'
    string_unavailable = "nvidia_temp: N/A"

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'temp_separator',
                    'new': 'string_separator',
                    'msg': 'obsolete parameter use `string_separator`',
                },
            ],
        }

    def nvidia_temp(self):
        out = check_output(shlex.split("nvidia-smi -q -d TEMPERATURE"))
        temps = re.findall(TEMP_RE, out.decode("utf-8"))

        if temps != []:
            data = []
            for temp in temps:
                data.append(self.py3.safe_format(self.format_temp, {'temp': temp}))

            data = self.py3.composite_join(self.string_separator, data)
            color = self.py3.COLOR_GOOD
            full_text = self.py3.safe_format(self.format, {'format_temp': data})
        else:
            color = self.py3.COLOR_BAD
            full_text = self.py3.safe_format(self.format,
                                             {'format_temp': self.string_unavailable})
        return {
            'full_text': full_text,
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
