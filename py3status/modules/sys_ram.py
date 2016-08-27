# -*- coding: utf-8 -*-
"""
Display the percent RAM used
This modules requires the psutil python module.

Configuration parameters:
    threshold_degraded / threshold_bad: thresholds for color change
    format: format string
        (defaut: "⚛{ram:3d}%")

Format status string parameters:
    {ram} ram usage in percent
"""

# import your useful libs here
import psutil


class Py3status:
    def __init__(self):
        self.threshold_degraded = 40
        self.threshold_bad = 75
        self.cache_timeout = 1
        self.format = "⚛{ram:3d}%"
        pass

    def used_ram(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': ''
        }
        used_mem_percent = round(psutil.virtual_memory().percent)
        if used_mem_percent <= self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif used_mem_percent <= self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        response['full_text'] = self.py3.safe_format(self.format,
                {'ram': used_mem_percent})

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
