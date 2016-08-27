# -*- coding: utf-8 -*-
"""
Display the load average.

Configuration parameters:
    threshold_degraded / threshold_bad: thresholds for color change
    format: format string
        (default: "{one:.2f} {five:.2f} {fifteen:.2f}")

Format status string parameters:
    {one} load average over the last minute
    {five} load average over the last five minutes
    {fifteen} load average over the last fifteen minutes
"""

# import your useful libs here
import os


class Py3status:
    def __init__(self):
        self.threshold_degraded = 2
        self.threshold_bad = 4
        self.cache_timeout = 5
        self.format = "{one:.2f} {five:.2f} {fifteen:.2f}"
        pass

    def load(self, i3s_output_list, i3s_config):
        one, five, fifteen = os.getloadavg()
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': ''
        }
        if one < self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif one < self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        response['full_text'] = self.py3.safe_format(self.format, {
            'one': one,
            'five': five,
            'fifteen': fifteen,
            })

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
