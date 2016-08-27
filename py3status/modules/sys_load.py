# -*- coding: utf-8 -*-
"""
Display the load average.

Configuration parameters:
    threshold_degraded / threshold_bad: thresholds for color change
"""

# import your useful libs here
from time import time
import os


class Py3status:
    # available configuration parameters
    threshold_degraded = 2
    threshold_bad = 4
    cache_timeout = 5

    def __init__(self):
        pass

    def load(self, i3s_output_list, i3s_config):
        one, five, fifteen = os.getloadavg()
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }
        if one < self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif one < self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        response['full_text'] = "{:.2f} {:.2f} {:.2f}".format(one, five, fifteen)

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
