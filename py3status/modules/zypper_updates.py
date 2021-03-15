"""
Display number of pending updates for OpenSUSE Linux.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 600)
    format: Display format to use
        (default 'zypper: [\?color=update {update}]')
    thresholds: specify color thresholds to use
        (default [(0, 'good'), (50, 'degraded'), (100, 'bad')])

Format placeholders:
    {updates} number of pending zypper updates

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author Ioannis Bonatakis <ybonatakis@suse.com>
@license BSD

SAMPLE OUTPUT
[{'full_text': 'zypper: '}, {'full_text': '0', 'color': '#00FF00'}]
"""

import subprocess
import re


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 600
    format = "zypper: [\?color=update {update}]"
    thresholds = [(0, "good"), (50, "degraded"), (100, "bad")]

    def post_config_hook(self):
        self.thresholds_init = self.py3.get_color_names_list(self.format)
        self.reg_ex_pkg = re.compile(b"v\\s\\S+", re.M)

    def zypper_updates(self):
        output, error = subprocess.Popen(
            ["zypper", "lu"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()

        zypper_data = {
            "update": len(self.reg_ex_pkg.findall(output)),
        }

        for x in self.thresholds_init:
            if x in zypper_data:
                self.py3.threshold_get_color(zypper_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, zypper_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
