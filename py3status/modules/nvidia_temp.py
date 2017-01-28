# -*- coding: utf-8 -*-
"""
Display NVIDIA GPU temperatures.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'GPU: {format_temp}')
    format_temp: display format for temperatures (default '{temp}°C')
    string_separator: display separator (only if more than one) (default '|')
    string_unavailable: display unavailable (default 'nvidia_temp: N/A')

Format placeholders:
    {format_temp} display format for temperatures

format_temp placeholders:
    {temp} current temperatures

Color options:
    color_bad: Temperature unavailable
    color_good: Temperature available

Requires:
    nvidia-smi:

@author jmdana <https://github.com/jmdana>
@license BSD
"""

import re


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
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        temps = self.py3.command_output("nvidia-smi -q -d TEMPERATURE")
        temps = re.findall(re.compile(r"Current Temp\s+:\s+([0-9]+)"), temps)

        if temps == []:
            response['cached_until'] = self.py3.CACHE_FOREVER
            response['color'] = self.py3.COLOR_BAD
            response['full_text'] = self.string_unavailable
        else:
            data = []
            for temp in temps:
                data.append(self.py3.safe_format(self.format_temp, {'temp': temp}))

            data = self.py3.composite_join(self.string_separator, data)
            data = self.py3.safe_format(self.format, {'format_temp': data})

            response['color'] = self.py3.COLOR_GOOD
            response['full_text'] = data

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
