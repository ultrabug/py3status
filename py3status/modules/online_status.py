# -*- coding: utf-8 -*-
"""
Determine if you have an Internet Connection.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{icon}')
    icon_off: show when connection is offline (default '■')
    icon_on: show when connection is online (default '●')
    timeout: time to wait for a response, in seconds (default 2)
    url: specify URL to connect when checking for a connection
        (default 'https://www.google.com')

Format placeholders:
    {icon} connection status

Color options:
    color_off: Connection offline, defaults to color_bad
    color_on: Connection online, defaults to color_good

@author obb


SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf'}

off
{'color': '#FF0000', 'full_text': u'\u25a0'}
"""

try:
    from urllib.request import urlopen, URLError  # py3
except ImportError:
    from urllib2 import urlopen, URLError  # py2


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{icon}"
    icon_off = u"■"
    icon_on = u"●"
    timeout = 2
    url = "https://www.google.com"

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "format_online",
                    "new": "icon_on",
                    "msg": "obsolete parameter use `icon_on`",
                },
                {
                    "param": "format_offline",
                    "new": "icon_off",
                    "msg": "obsolete parameter use `icon_off`",
                },
            ]
        }

    def post_config_hook(self):
        self.color_on = self.py3.COLOR_ON or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_OFF or self.py3.COLOR_BAD
        self.ping_command = ["ping", "-c", "1", "-W", "%s" % self.timeout, self.url]

    def _connection_present(self):
        if "://" in self.url:
            try:
                urlopen(self.url, timeout=self.timeout)
                return True
            except URLError:
                return False
        else:
            try:
                self.py3.command_output(self.ping_command)
                return True
            except self.py3.CommandError:
                return False

    def online_status(self):
        if self._connection_present():
            icon = self.icon_on
            color = self.color_on
        else:
            color = self.color_off
            icon = self.icon_off

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"icon": icon}),
            "color": color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
