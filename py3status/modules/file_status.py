# -*- coding: utf-8 -*-
"""
Display if a file or dir exists.

Configuration parameters:
    cache_timeout: how often to run the check
    format_available: what to display when available
    format_unavailable: what to display when unavailable
    path: check if file or dir exists

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
    format_available = u'●'
    format_unavailable = u'■'
    path = '/dev/sdb1'

    def file_status(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout
        }

        fnull = open(os.devnull, 'w')
        if subprocess.call(["ls", self.path], stdout=fnull, stderr=fnull) == 0:
            response['full_text'] = self.format_available
            response['color'] = i3s_config['color_good']
        else:
            response['full_text'] = self.format_unavailable
            response['color'] = i3s_config['color_bad']

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
        print(x.file_status([], config))
        sleep(1)
