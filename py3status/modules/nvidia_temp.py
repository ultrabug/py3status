# -*- coding: utf-8 -*-
"""
Display NVIDIA GPU temperature.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'GPU: {format_temp}')
    format_temp: display format for temperatures (default '{temp}°C')
    temp_separator: temperature separator (if more than one) (default '|')

Format placeholders:
    {format_temp} format for temperatures

format_temp placeholders:
    {temp} temperatures

Color options:
    color_bad: Unavailable
    color_good: Available

Requires:
    nvidia-smi: NVIDIA System Management Interface program

@author jmdana <https://github.com/jmdana>
@license BSD

SAMPLE OUTPUT
{'full_text': 'GPU: 62°C', 'color': '#00FF00'}
"""

import re

TEMP_RE = re.compile(r"Current Temp\s+:\s+([0-9]+)")
STRING_NOT_INSTALLED = "not installed"
STRING_UNAVAILABLE = "nvidia_temp: N/A"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "GPU: {format_temp}"
    format_temp = u"{temp}°C"
    temp_separator = "|"

    class Meta:
        def deprecate_function(config):
            out = {}
            if "format_units" in config:
                out["format_temp"] = u"{{temp}}{}".format(config["format_units"])
            if "format_prefix" in config:
                out["format"] = u"{}{{format_temp}}".format(config["format_prefix"])
            return out

        deprecated = {"function": [{"function": deprecate_function}]}

    def post_config_hook(self):
        if not self.py3.check_commands("nvidia-smi"):
            raise Exception(STRING_NOT_INSTALLED)

    def nvidia_temp(self):
        temps = self.py3.command_output("nvidia-smi -q -d TEMPERATURE")
        temps = set(TEMP_RE.findall(temps))
        if temps == []:
            return {
                "cached_until": self.py3.CACHE_FOREVER,
                "color": self.py3.COLOR_BAD,
                "full_text": STRING_UNAVAILABLE,
            }
        data = []
        for temp in temps:
            data.append(self.py3.safe_format(self.format_temp, {"temp": temp}))
        data = self.py3.composite_join(self.temp_separator, data)
        full_text = self.py3.safe_format(self.format, {"format_temp": data})

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": self.py3.COLOR_GOOD,
            "full_text": full_text,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
