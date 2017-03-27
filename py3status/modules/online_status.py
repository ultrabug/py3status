# -*- coding: utf-8 -*-
"""
Determine if you have an Internet Connection.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{icon}')
    icon_off: show when connection is offline (default '■')
    icon_on: show when connection is online (default '●')
    timeout: how many seconds before we announce offline (default 2)
    url: name of url to use when checking for a connection
         (default 'http://www.google.com')

Format placeholders:
    {icon} status icon

Color options:
    color_bad: Offline
    color_good: Online

@author obb
"""

try:
    # python 3
    from urllib.parse import urlsplit
    from urllib.request import urlopen
except ImportError:
    # python 2
    from urlparse import urlsplit
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

    def post_config_hook(self):
        self.color_on = self.py3.COLOR_ON or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_OFF or self.py3.COLOR_BAD
        self.use_ping = None

        if '://' in self.url:
            self.ping_url = urlsplit(self.url).netloc

    def _ping(self):
        try:
            self.py3.command_output(['ping', '-c', '1', self.ping_url])
            return True
        except:
            return False

    def _urlopen(self):
        try:
            urlopen(self.url, timeout=self.timeout)
            return True
        except:
            return False

    def online_status(self):
        icon = self.icon_off
        color = self.color_off

        if self.use_ping:
            self.py3.log("if use_ping: was true.")
            if self._ping():
                self.py3.log("...if ping (in ping), ping was good.")
                icon = self.icon_on
                color = self.color_on
                self.use_ping = True
            else:
                self.py3.log("... if ping (in ping) ping was bad.")
                self.use_ping = False
        elif self._urlopen():
            self.py3.log("elif urlopen: was true.")
            icon = self.icon_on
            color = self.color_on
            if self._ping():
                self.py3.log("... if ping (in urlopen), ping was good.")
                self.use_ping = True
            else:
                self.py3.log("... if ping (in urlopen), ping was bad.")
                self.use_ping = False

        if self.use_ping is None:
            self.py3.log("if use_ping: was None.")
            if self._ping():
                self.py3.log("...if ping (in use_ping), ping was good.")
                self.use_ping = True
                icon = self.icon_on
                color = self.color_on
            else:
                self.py3.log("...if ping (in use_ping), ping was bad.")
                self.use_ping = False

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'icon': icon}),
            'color': color}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
