# -*- coding: utf-8 -*-
"""
Display if a process is running.

Configuration parameters:
    cache_timeout: how often to run the check
    format_running: what to display when process running
    format_not_running: what to display when process is not running
    process: check if process is running

@author obb, Moritz Lüdecke
"""

from time import time
import os
import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format_running = u'●'
    format_not_running = u'■'
    process = 'rsnapshot'

    def process_status(self, i3s_output_list, i3s_config):
        text = self.format_not_running
        color = i3s_config['color_bad']

        fnull = open(os.devnull, 'w')
        if subprocess.call(["pgrep", self.process],
                           stdout=fnull, stderr=fnull) == 0:
            text = self.format_running
            color = i3s_config['color_good']

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': text,
            'color': color
        }

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
