# -*- coding: utf-8 -*-
"""
Determine if you have an Internet Connection.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format: display format for online_status (default '{icon}')
    icon_off: what to display when offline (default '■')
    icon_on: what to display when online (default '●')
    timeout: how long before deciding we're offline (default 2)
    url: connect to this url to check the connection status
         (default 'http://www.google.com')

Format placeholders:
    {icon} display current online status

Color options:
    color_bad: Offline
    color_good: Online

@author obb


SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf'}

off
{'color': '#FF0000', 'full_text': u'\u25a0'}
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
    format = '{icon}'
    icon_off = u'■'
    icon_on = u'●'
    timeout = 2
    url = 'http://www.google.com'

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'format_online',
                    'new': 'icon_on',
                    'msg': 'obsolete parameter use `icon_on`',
                },
                {
                    'param': 'format_offline',
                    'new': 'icon_off',
                    'msg': 'obsolete parameter use `icon_off`',
                },
            ],
        }

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

        if self._connection_present():
            response = {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format, {'icon': self.icon_on}),
                'color': self.py3.COLOR_GOOD
            }
        else:
            response = {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format, {'icon': self.icon_off}),
                'color': self.py3.COLOR_BAD
            }

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
