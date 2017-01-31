# -*- coding: utf-8 -*-
"""
Display status of a TCP port on a given host.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{host}:{port} {state}')
    host: check host (default 'localhost')
    port: check port number (default 22)
    string_down: show string when available (default 'UP')
    string_up: show string when unavailable (default 'DOWN')

Format placeholders:
    {state} port state

Color options:
    color_down: Unavailable, default color_bad
    color_up: Available, default color_good

@author obb, Moritz Lüdecke
"""

import socket


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{host}:{port} {state}'
    host = 'localhost'
    port = 22
    string_down = 'DOWN'
    string_up = 'UP'

    def post_config_hook(self):
        self.color_on = self.py3.COLOR_UP or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_DOWN or self.py3.COLOR_BAD

    def check_tcp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.host, self.port))
        state = self.string_down if result else self.string_up

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'state': state}),
            'color': self.color_off if result else self.color_on
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
