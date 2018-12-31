# -*- coding: utf-8 -*-
"""
Display current CPU clock speed as reported in /proc/cpuinfo

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module
        *(default '{avg} GHz, {max} GHz')*

Format placeholders:
    {avg} average frequency across all cores
    {max} highest clock frequency

Example:
```
# shows average and max frequencies every three seconds:
cpufreq {
    format = '{avg} GHz, {max} GHz'
    cache_timeout = 3
}

@author JackDoan
@license BSD

"""

from functools import reduce


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = (
        "{avg} GHz, {max} GHz"
    )

    # perhaps this could be a parameter one day?
    cmd = "cat /proc/cpuinfo | grep MHz | cut -d : -f 2"

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {
                        "max": ":.2f",
                        "avg": ":.2f",
                    },
                    "format_strings": ["format"],
                }
            ]
        }

    @staticmethod
    def _process_core_str(core_str):
        val = core_str.strip()
        val = float(val)
        return val

    def _get_all_core_freqs(self):
        out = self.py3.command_output(self.cmd, True)  # run in shell
        cores_str = out.split('\n', 256)
        del cores_str[-1]  # remove trailing newline
        cores = list(map(lambda x: self._process_core_str(x), cores_str))
        return cores

    def cpufreq(self):
        cores = self._get_all_core_freqs()
        avg = reduce(lambda x, y: x + y, cores) / len(cores)

        data = {
            'avg': avg / 1000,        # convert to GHz
            'max': max(cores) / 1000  # convert to GHz
        }

        return {
            'full_text': self.py3.safe_format(self.format, data),
            'cached_until': self.py3.time_in(self.cache_timeout, 1)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
