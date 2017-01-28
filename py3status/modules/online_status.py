# -*- coding: utf-8 -*-
"""
Determine if you have an Internet Connection.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{icon}')
    icon_off: display icon when offline (default '■')
    icon_on: display icon when online (default '●')
    url: connect to this url to check the connection status
         (default 'http://www.google.com')

Format placeholders:
    {icon} display current online status

Color options:
    color_bad: Offline
    color_good: Online

@author obb
"""

try:
    # python 3
    from urllib.parse import urlsplit
except ImportError:
    # python 2
    from urlparse import urlsplit


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{icon}'
    icon_off = u'■'
    icon_on = u'●'
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
            'remove': [
                {
                    'param': 'timeout',
                    'msg': 'obsolete parameter',
                },
            ]
        }

    def post_config_hook(self):
        self.color_on = self.py3.COLOR_ON or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_OFF or self.py3.COLOR_BAD
        if '://' in self.url:
            self.url = urlsplit(self.url).netloc

    def _connection_present(self):
        try:
            self.py3.command_output(['ping', '-c', '1', self.url])
        except:
            return False
        else:
            return True

    def online_status(self):
        run = self._connection_present()
        icon = self.icon_on if run else self.icon_off

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'icon': icon}),
            'color': self.color_on if run else self.color_off
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
