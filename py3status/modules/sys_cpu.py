# -*- coding: utf-8 -*-
"""
Display the percent CPU used.
This modules requires the psutil python module.

Configuration parameters:
    threshold_degraded / threshold_bad: thresholds for color change
"""

# import your useful libs here
from time import time
import psutil


class Py3status:
    # available configuration parameters
    threshold_degraded = 50
    threshold_bad = 80
    cache_timeout = 1

    def __init__(self):
        pass

    def cpu_percent(self, i3s_output_list, i3s_config):
        cpu = round(psutil.cpu_percent())
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }
        if cpu < self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif cpu < self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        response['full_text'] = "☢{:3d}%".format(cpu)

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
