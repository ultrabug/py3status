# -*- coding: utf-8 -*-
"""
Display if a connection to the internet is established.

Configuration parameters:
    cache_timeout: how often to run the check
    format_offline: what to display when offline
    format_online: what to display when online
    timeout: how long before deciding we're offline
    url: connect to this url to check the connection status

@author obb
"""

from time import time
import os
import re
try:
    # python3
    from urllib.request import urlopen
except:
    from urllib2 import urlopen


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format_offline = u'■'
    format_online = u'●'
    timeout = 2
    url = 'http://www.google.com'

    def _connection_present(self):
        if re.search('://', self.url):
            try:
                urlopen(self.url, timeout=self.timeout)
            except:
                return False
            else:
                return True
        else:
            if os.system("ping -c 1 " + self.url + ">> /dev/null 2>&1") == 0:
                return True
            else:
                return False

    def online_status(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout
        }

        connected = self._connection_present()
        if connected:
            response['full_text'] = self.format_online
            response['color'] = i3s_config['color_good']
        else:
            response['full_text'] = self.format_offline
            response['color'] = i3s_config['color_bad']

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.online_status([], config))
        sleep(1)
