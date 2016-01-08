"""
Display the current wifi ESSID and IP address.

It improves on the default i3status wifi module by allowing the user
to toggle between the ESSID and IP address with a mouse click.

This module is inspired by the "whatismyip" module.

Requires:
    - iwlib (https://pypi.python.org/pypi/iwlib)

Configuration parameters:
    - mode: default mode to display. Can be 'essid' or 'ip'
    - interface: the wireless interface to query. (default wlan0)

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD
"""

import iwlib
import socket
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    mode = 'essid'
    interface = 'wlan0'

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Toggle between display modes 'essid' and 'ip'
        """
        if self.mode == 'essid':
            self.mode = 'ip'
        else:
            self.mode = 'essid'

    def _get_status(self):
        result = iwlib.get_iwconfig(self.interface)
        quality = result['stats']['quality']
        essid = bytes(result['ESSID']).decode()
        return (essid, quality, socket.gethostbyname(socket.gethostname()))

    def wifi(self, i3s_output_list, i3s_config):
        """
        """
        (essid, quality, ip) = self._get_status()
        response = {'cached_until': time() + self.cache_timeout}

        if(self.mode == 'essid'):
            response['full_text'] = essid
        else:
            response['full_text'] = ip

        if(quality < 25):
            response['color'] = i3s_config['color_bad']
        if(quality >= 25 and quality < 50):
            response['color'] = i3s_config['color_degraded']
        if(quality >= 75):
            response['color'] = i3s_config['color_good']

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.wifi([], config))
        sleep(1)
