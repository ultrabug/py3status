# -*- coding: utf-8 -*-
"""
Display the CPU temperature

Configuration parameters:
    zone: temperature zone to check.
        (default: 'coretemp-isa-0000')
"""

# import your useful libs here
from time import time
import subprocess


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    threshold_degraded = 80
    threshold_bad = 100
    zone = 'coretemp-isa-0000'

    def __init__(self):
        pass

    def cpu_temp(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }
        temp = float(subprocess.check_output(['sensors',self.zone]).split()[7].decode("utf-8")[1:-2])
        if temp < self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif temp < self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        response['full_text'] = "{:.1f}°C".format(temp)

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
