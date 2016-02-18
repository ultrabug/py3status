# -*- coding: utf-8 -*-
"""
Display WiFi bit rate, quality, signal and SSID using iw.

Configuration parameters:
    - cache_timeout : Update interval in seconds (default: 5)
    - device : Wireless device name (default: "wlan0")
    - down_color : Output color when disconnected, possible values:
      "good", "degraded", "bad" (default: "bad")
      percent (default: false)
    - signal_bad : Bad signal strength in percent (default: 29)
    - signal_degraded : Degraded signal strength in percent
      (default: 49)
    - bitrate_bad : Bad bit rate in Mbit/s (default: 26)
    - bitrate_degraded : Degraded bit rate in Mbit/s (default: 53)
    - round_bitrate : If true, bitrate is rounded to the nearest whole number
      (default: true)
    - format_up : See placeholders below (default:
      "W: {bitrate} {signal_percent} {ssid}").
    - format_down : Output when disconnected (default: "down")

Format of status string placeholders:
    {bitrate} - Display bit rate
    {signal_percent} - Display signal in percent
    {signal_dbm} - Display signal in dBm
    {ssid} - Display SSID

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
    down_color = 'bad'
    signal_percent_bad = 29
    signal_percent_degraded = 49
    bitrate_bad = 26
    bitrate_degraded = 53
    round_bitrate = True
    format_up = 'W: {bitrate} {signal_percent} {ssid}'
    format_down = 'W: down'

    def get_wifi(self, i3s_output_list, i3s_config):
        """
        Get WiFi status using iw.
        """
        self.signal_dbm_bad = self._percent_to_dbm(self.signal_percent_bad)
        self.signal_dbm_degraded = \
            self._percent_to_dbm(self.signal_percent_degraded)

        iw = subprocess.check_output(['iw', self.device, 'link']).decode(
            'utf-8')

        bitrate_out = re.search('tx bitrate: ([^\s]+) ([^\s]+)', iw)
        if bitrate_out:
            bitrate = float(bitrate_out.group(1))
            if self.round_bitrate:
                bitrate = round(bitrate)
            bitrate_unit = bitrate_out.group(2)
            if bitrate_unit == 'Gbit/s':
                bitrate *= 1000
        else:
            bitrate = None
            bitrate_unit = None
        signal_out = re.search('signal: ([\-0-9]+)', iw)
        if signal_out:
            signal_dbm = int(signal_out.group(1))
            signal_percent = min(self._dbm_to_percent(signal_dbm), 100)
        else:
            signal_dbm = None
            signal_percent = None
        ssid_out = re.search('SSID: (.+)', iw)
        if ssid_out:
            ssid = ssid_out.group(1)
        else:
            ssid = None

        if ssid is None:
            full_text = self.format_down
            color = i3s_config['color_{}'.format(self.down_color)]
        else:
            if bitrate <= self.bitrate_bad or \
                    signal_dbm <= self.signal_dbm_bad:
                color = i3s_config['color_bad']
            elif bitrate <= self.bitrate_degraded or \
                    signal_dbm <= self.signal_dbm_degraded:
                color = i3s_config['color_degraded']
            else:
                color = i3s_config['color_good']

            bitrate = '{} {}'.format(bitrate, bitrate_unit)
            signal_percent = '{}%'.format(signal_percent)
            signal_dbm = '{} dBm'.format(signal_dbm)

            full_text = self.format_up.format(bitrate=bitrate,
                                              signal_percent=signal_percent,
                                              signal_dbm=signal_dbm,
                                              ssid=ssid)

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': full_text,
            'color': color
        }
        return response

    def _percent_to_dbm(self, percent):
        return (percent / 2) - 100

    def _dbm_to_percent(self, dbm):
        return 2 * (dbm + 100)


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
