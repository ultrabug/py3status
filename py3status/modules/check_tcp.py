# -*- coding: utf-8 -*-
"""
Display status of a TCP port on a given host.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format: what to display on the bar (default '{host}:{port} {state}')
    host: check if tcp port on host is up (default 'localhost')
    port: the tcp port (default 22)

Format placeholders:
    {state} port state ('DOWN' or 'UP')

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

    def check_tcp(self):
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.host, self.port))

        if result == 0:
            state = 'UP'
            response['color'] = self.py3.COLOR_UP or self.py3.COLOR_GOOD
        else:
            state = 'DOWN'
            response['color'] = self.py3.COLOR_DOWN or self.py3.COLOR_BAD

        response['full_text'] = self.py3.safe_format(self.format,
                                                     {'state': state})
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
