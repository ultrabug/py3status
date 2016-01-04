"""
Display your wifi essid and IP address.
This module improves the default wifi module by having two display modes
that can toggled with a mouse click. This saves space in the status bar.

This module is inspired by the "whatismyip" module.

Requires:
    - iwlib (https://pypi.python.org/pypi/iwlib)

Configuration parameters:
    - mode: default mode to display. Can be '{essid}' or '{ip}'
    - interface: the wireless interface to query (default wlan0)

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
    cache_timeout = 30
    mode = 'essid'
    negative_cache_timeout = 2
    timeout = 5

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Toggle between display modes 'essid' and 'ip'
        """
        if self.mode == 'essid':
            self.mode = 'ip'
        else:
            self.mode = 'essid'

    def _get_status(self, interface):
        interface = iwlib.get_iwconfig(interface)
        quality = interface['stats']['quality']
        essid = bytes(interface['ESSID']).decode()
        return (essid, quality, socket.gethostbyname(socket.gethostname()))

    def wifi(self, i3s_output_list, i3s_config):
        """
        """
        (essid, quality, ip) = self._get_status(self.interface)
        response = {'cached_until': time() + self.negative_cache_timeout}

        if(self.mode == 'essid'):
            response['full_text'] = essid
        else:
            response['full_text'] = ip

        if(quality < 33):
            response['color'] = i3s_config['color_bad']
            
        if(quality >= 66):
            response['color'] = i3s_config['color_good']

        return response


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'interface': 'wlan0',
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.wifi([], config))
        sleep(1)
