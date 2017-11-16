# -*- coding: utf-8 -*-
"""
Display whether a hostname or IP address responds to pings.

This module pings a specified hostname or IP address and displays whether the
host is "up" or "down". The ping timeout, up text, and down text are configurable.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 2)
    down_text: text to display if host does not respond (default '{host} is down')
    host: hostname or IP address to ping (default "www.google.com")
    ping_timeout: seconds to wait for ping responses (default 2)
    up_text: text to display if host responds (default '{host} is up')

Format placeholders:
    {host} The host or IP address set in the "host" configuration parameter.

Examples:

ping_host {
  host = "www.google.com"
  ping_timeout = 1
  up_text "Google is up"
  down_text "Google is down"
}

ping_host {
  host = "myraspberrypi"
  ping_tieout = 2
}

SAMPLE OUTPUT
up
{
    'color': '#00FF00',
    'full_text': u'www.google.com is up',
    'cached_until': 1510792199.0
}

down
{
    'color': '#FF0000',
    'full_text': u'www.google.com is down',
    'cached_until': 1510792199.0
}

@author Micah Strube <micah.strube@me.com>

"""

from os import system as system_call


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 2
    down_text = '{host} is down'
    host = 'www.google.com'
    ping_timeout = 2
    up_text = '{host} is up'

    def ping_host(self):
        ping_cmd = "ping -c 1 -W {t} {h} > /dev/null".format(
                t=self.ping_timeout,
                h=self.host)

        is_up = system_call(ping_cmd) == 0

        if is_up:
            status = 'up'
            color = self.py3.COLOR_GOOD
            text = self.up_text
        else:
            status = 'down'
            color = self.py3.COLOR_BAD
            text = self.down_text

        response = {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'color': color,
                'full_text': self.py3.safe_format(text,
                                                  {
                                                      'host': self.host,
                                                      'status': status,
                                                  })
        }

        print response
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
