# -*- coding: utf-8 -*-
"""
Display if a file or dir exists.

Configuration parameters:
    cache_timeout: how often to run the check
    color_running: color of format_running
    color_not_running: color of format_not_running
    format_running: what to display when process running
    format_not_running: what to display when process is not running
    process: check if process is running

@author obb, Moritz Lüdecke
"""

from time import time
import os

class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    color_running = None
    color_not_running = None
    format_running = u'●'
    format_not_running = u'■'
    process = 'rsnapshot'

    def process_status(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout
        }

        if os.system("pgrep " + self.process + " >> /dev/null 2>&1") == 0:
            response['full_text'] = self.format_running
            response['color'] = self.color_running or i3s_config['color_good']
        else:
            response['full_text'] = self.format_not_running
            response['color'] = self.color_not_running or i3s_config['color_bad']

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.process_status([], config))
        sleep(1)
