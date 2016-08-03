# -*- coding: utf-8 -*-
"""
Display if a file or dir exists.

Configuration parameters:
    cache_timeout: how often to run the check
    format_available: what to display when available
    format_unavailable: what to display when unavailable
    path: the path to a file or dir to check if it exists

@author obb, Moritz Lüdecke
"""

from time import time
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

    def _get_text(self, i3s_config):
        fnull = open(os.devnull, 'w')
        if subprocess.call(["ls", self.path], stdout=fnull, stderr=fnull) == 0:
            text = self.format_available
            color = i3s_config['color_good']
        else:
            text = self.format_unavailable
            color = i3s_config['color_bad']

        return (color, text)

    def file_status(self, i3s_output_list, i3s_config):
        if self.path is None:
            color = i3s_config['color_bad']
            text = ERR_NO_PATH
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
