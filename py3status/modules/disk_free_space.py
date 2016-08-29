# -*- coding: utf-8 -*-
"""
Display the amount of free space of given disk.
This modules requires the psutil python module.

Configuration parameters:
    path: filesystem path to check
        (default: "/")
    format: format string
        (default: "{space:.1f}G")
    threshold_bad: use color_bad below this
    threshold_degraded: use color_degraded between this and threshold_bad

Format string parameters:
    {space} space left (in GB)
    {path} path checked
"""

# import your useful libs here
import psutil


class Py3status:
    cache_timeout = 10
    threshold_degraded = 50
    threshold_bad = 10
    path = "/"
    format = '{space:.1f}G'

    def __init__(self):
        pass

    def disk_usage(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': '',
        }
        space = psutil.disk_usage(self.path).free / 1024 / 1024 / 1024
        if space < self.threshold_bad:
            response['color'] = self.py3.COLOR_BAD
        elif space < self.threshold_degraded:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_GOOD
        response['full_text'] = self.py3.safe_format(self.format, {
            'path': self.path,
            'space': space,
            })

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
