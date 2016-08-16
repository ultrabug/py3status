# -*- coding: utf-8 -*-
"""
Display if a TCP port is available on the given host.

Configuration parameters:
    cache_timeout: how often to run the check, default 10s
    color_down: color of format_down
    color_up: color of format_up
    format_down: what to display when tcp port is down
    format_up: what to display when tcp port is up
    host: check if tcp port on host is up, default localhost
    port: the tcp port, default 22

@author obb, Moritz Lüdecke
"""

from time import time
import socket


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    color_down = None
    color_up = None
    format_down = '{host}:{port} is down'
    format_up = '{host}:{port} is up'
    host = 'localhost'
    port = 22

    def check_tcp(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout)
        }

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.host, self.port))

        if result == 0:
            response['full_text'] = self.py3.safe_format(self.format_up,
                                                         {'host': self.host,
                                                          'port': self.port})
            response['color'] = self.color_up or self.py3.COLOR_GOOD
        else:
            response['full_text'] = self.py3.safe_format(self.format_down,
                                                         {'host': self.host,
                                                          'port': self.port})
            response['color'] = self.color_down or self.py3.COLOR_BAD

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
