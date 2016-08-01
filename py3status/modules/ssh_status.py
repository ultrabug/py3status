# -*- coding: utf-8 -*-
"""
Display if a ssh on host is available

Configuration parameters:
    cache_timeout: how often to run the check
    color_down: color of format_down
    color_up: color of format_up
    format_down: what to display when ssh server is donw
    format_up: what to display when ssh server is up
    host: check if ssh service on host is up
    port: the port
    timeout: the time which the server has to answer

Requires:
    netcat

@author obb, Moritz Lüdecke
"""

from time import time
import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    color_down = None
    color_up = None
    format_down = 'SSH down'
    format_up = 'SSH up'
    host = 'localhost'
    port = 22
    timeout = 1

    def ssh_status(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout
        }

        cmd = ['netcat', '-w', str(self.timeout), self.host, str(self.port)]

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            ssh_connectable = 'SSH' in str(output)
        except Exception:
            ssh_connectable = False

        if ssh_connectable:
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
