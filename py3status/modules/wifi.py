# -*- coding: utf-8 -*-
"""
Display WiFi quality or signal, and bitrate using iw.

Configuration parameters:
    - cache_timeout : Update interval in seconds (default: 5)
    - device : Wireless device name (default: "wlan0")
    - label : Left-sided label (default: "W: ")
    - down_text : Output when disconnected (default: "down")
    - down_color : Output color when disconnected, possible values:
      "good", "degraded", "bad" (default: "bad")
    - signal_dbm : If true, displays signal in dBm instead of quality in
      percent (default: false)
    - signal_bad : Bad signal strength in dBm, or percent if signal_quality is
      true (default: -85)
    - signal_degraded : Degraded signal strength in dBm, or percent if
      signal_quality is true (default: -75)
    - rate_bad : Bad bitrate in Mbit/s (default: 26)
    - rate_degraded : Degraded bitrate in Mbit/s (default: 53)

Requires:
    - iw

@author Markus Weimar <mail@markusweimar.de>
@license BSD
"""

import re
import subprocess
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    device = 'wlan0'
    label = 'W: '
    down_text = 'down'
    down_color = 'bad'
    signal_dbm = False
    signal_bad = -85
    signal_degraded = -75
    rate_bad = 26
    rate_degraded = 53

    def get_wifi(self, i3s_output_list, i3s_config):
        """
        Get signal and bitrate using iw.
        """
        wifi = subprocess.check_output(['iw', self.device, 'link']).decode(
            'utf-8')

        rate_out = re.search('tx bitrate: ([0-9\.]+)', wifi)
        if rate_out:
            rate_num = round(float(rate_out.group(1)))
        else:
            rate_num = None

        signal_out = re.search('signal: ([\-0-9]+)', wifi)
        if signal_out:
            signal_num = int(signal_out.group(1))
        else:
            signal_num = None

        if any(num is None for num in [rate_num, signal_num]):
            full_text = self.label + self.down_text
            color = i3s_config['color_{}'.format(self.down_color)]
        else:
            if rate_num <= self.rate_bad or signal_num <= self.signal_bad:
                color = i3s_config['color_bad']
            elif rate_num <= self.rate_degraded or \
                    signal_num <= self.signal_degraded:
                color = i3s_config['color_degraded']
            else:
                color = i3s_config['color_good']
            if self.signal_dbm is True:
                signal_unit = ' dBm'
            else:
                signal_unit = '%'
                signal_num = 2 * (signal_num + 100)
            full_text = self.label + str(rate_num) + ' MBit/s' + ' ' + \
                str(signal_num) + signal_unit

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': full_text,
            'color': color
        }
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    This SHOULD work before contributing your module please.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.get_wifi([], config))
        sleep(1)
