# -*- coding: utf-8 -*-
"""
Display if a connection to the internet is established.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format_offline: what to display when offline (default '■')
    format_online: what to display when online (default '●')
    timeout: how long before deciding we're offline (default 2)
    url: connect to this url to check the connection status
         (default 'http://www.google.com')

Color options:
    color_bad: Offline
    color_good: Online

@author obb
"""

import os
import subprocess
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
        if '://' in self.url:
            try:
                urlopen(self.url, timeout=self.timeout)
            except:
                return False
            else:
                return True
        else:
            fnull = open(os.devnull, 'w')
            return subprocess.call(['ping', '-c', '1', self.url],
                                   stdout=fnull, stderr=fnull) == 0

    def online_status(self):
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout)
        }

        connected = self._connection_present()
        if connected:
            response['full_text'] = self.format_online
            response['color'] = self.py3.COLOR_GOOD
        else:
            response['full_text'] = self.format_offline
            response['color'] = self.py3.COLOR_BAD

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
