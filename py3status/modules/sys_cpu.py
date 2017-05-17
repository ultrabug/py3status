# -*- coding: utf-8 -*-
"""
Display the percent CPU used.
This modules requires the psutil python module.

Configuration parameters:
    format: format string to use
        (default: "☢{cpu:3d}%")
    threshold_degraded / threshold_bad: thresholds for color change

Format status string parameters:
    {cpu} cpu usage in percent
"""

# import your useful libs here
import psutil


class Py3status:
    def __init__(self):
        self.threshold_degraded = 50
        self.threshold_bad = 80
        self.cache_timeout = 1
        self.format = "☢{cpu:3d}%"
        pass

    def cpu_percent(self, i3s_output_list, i3s_config):
        cpu = round(psutil.cpu_percent())
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': ''
        }
        if cpu < self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif cpu < self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        response['full_text'] = self.py3.safe_format(self.format, {'cpu': cpu})

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
