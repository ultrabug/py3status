# -*- coding: utf-8 -*-
"""
Display the CPU temperature

Configuration parameters:
    zone: temperature zone to check.
        (default: 'coretemp-isa-0000')
    format: format string
        (default: '{temp:.1f}°C')
    threshold_bad/threshold_degraded: threshold for changing the color

Format status string parameters:
    {temp} the temperature measured
"""

# import your useful libs here
from time import time
import subprocess


class Py3status:
    def __init__(self):
        self.cache_timeout = 10
        self.threshold_degraded = 80
        self.threshold_bad = 100
        self.zone = 'coretemp-isa-0000'
        self.format = '{temp:.1f}°C'
        pass

    def cpu_temp(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': ''
        }
        temp = float(subprocess.check_output(['sensors',self.zone]).split()[7].decode("utf-8")[1:-2])
        if temp < self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif temp < self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        response['full_text'] = self.py3.safe_format(self.format, {'temp': temp})

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
