# -*- coding: utf-8 -*-
"""
Display if a process is running.

Configuration parameters:
    cache_timeout: how often to run the check
    format_running: what to display when process running
    format_not_running: what to display when process is not running
    process: the process name to check if it is running

@author obb, Moritz Lüdecke
"""

from time import time
import os
import subprocess

ERR_NO_PROCESS = 'no process name given'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format_running = u'●'
    format_not_running = u'■'
    process = None

    def _get_text(self, i3s_config):
        fnull = open(os.devnull, 'w')
        if subprocess.call(["pgrep", self.process],
                           stdout=fnull, stderr=fnull) == 0:
            text = self.format_running
            color = i3s_config['color_good']
        else:
            text = self.format_not_running
            color = i3s_config['color_bad']

        return (color, text)

    def process_status(self, i3s_output_list, i3s_config):
        if self.process is None:
            color = i3s_config['color_bad']
            text = ERR_NO_PROCESS
        else:
            (color, text) = self._get_text(i3s_config)

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': text,
            'color': color
        }

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
