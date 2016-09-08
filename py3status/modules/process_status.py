# -*- coding: utf-8 -*-
"""
Display if a process is running.

Configuration parameters:
    cache_timeout: how often to run the check
    format_running: what to display when process running
    format_not_running: what to display when process is not running
    process: the process name to check if it is running

Color options:
    color_bad: Process not running or error
    color_good: Process running

@author obb, Moritz Lüdecke
"""

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

    def _get_text(self):
        fnull = open(os.devnull, 'w')
        if subprocess.call(["pgrep", self.process],
                           stdout=fnull, stderr=fnull) == 0:
            text = self.format_running
            color = self.py3.COLOR_GOOD
        else:
            text = self.format_not_running
            color = self.py3.COLOR_BAD

        return (color, text)

    def process_status(self):
        if self.process is None:
            color = self.py3.COLOR_BAD
            text = ERR_NO_PROCESS
        else:
            (color, text) = self._get_text()

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
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
