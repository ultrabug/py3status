# -*- coding: utf-8 -*-
"""
Display the amount of free space of given disk.
This modules requires the psutil python module.

Configuration parameters:
    path: filesystem path to check
        (default: "/")
    threshold_degraded / threshold_bad: thresholds for color change
"""

# import your useful libs here
from time import time
import psutil


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    threshold_degraded = 50
    threshold_bad = 10
    path = "/"

    def __init__(self):
        pass

    def disk_usage(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }
        disk = psutil.disk_usage(self.path).free / 1024 / 1024 / 1024
        if disk < self.threshold_bad:
            response['color'] = self.py3.COLOR_BAD
        elif disk < self.threshold_degraded:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_GOOD
        response['full_text'] = "{:.1f}G".format(disk)

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
