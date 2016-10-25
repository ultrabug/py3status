# -*- coding: utf-8 -*-
"""
Display if a file or dir exists.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format_available: what to display when available (default '●')
    format_unavailable: what to display when unavailable (default '■')
    path: the path to a file or dir to check if it exists (default None)

Color options:
    color_bad: Error or file/directory does not exist
    color_good: File or directory exists

@author obb, Moritz Lüdecke
"""

import os
import subprocess

ERR_NO_PATH = 'no path given'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format_available = u'●'
    format_unavailable = u'■'
    path = None

    def _get_text(self):
        fnull = open(os.devnull, 'w')
        if subprocess.call(["ls", self.path], stdout=fnull, stderr=fnull) == 0:
            text = self.format_available
            color = self.py3.COLOR_GOOD
        else:
            text = self.format_unavailable
            color = self.py3.COLOR_BAD

        return (color, text)

    def file_status(self):
        if self.path is None:
            color = self.py3.COLOR_BAD
            text = ERR_NO_PATH
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
