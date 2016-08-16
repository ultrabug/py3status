# -*- coding: utf-8 -*-
"""
Display if a ssh on host is available

Configuration parameters:
    cache_timeout: how often to run the check
    color_down: color of format_down
    color_up: color of format_up
    format_down: what to display when tcp port is down
    format_up: what to display when tcp port is up
    host: check if tcp port on host is up
    port: the tcp port

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
    format_down = 'TCP port down'
    format_up = 'TCP port up'
    host = 'localhost'
    port = 22

    def check_tcp(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout
        }

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.host, self.port))

        if result == 0:
            response['full_text'] = self.format_up
            response['color'] = self.color_up or i3s_config['color_good']
        else:
            response['full_text'] = self.format_down
            response['color'] = self.color_down or i3s_config['color_bad']

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
