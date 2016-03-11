# -*- coding: utf-8 -*-
"""
Display dropboxd status.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (10s default)
    format: prefix text for the dropbox status

Valid status values include:
    - Dropbox isn't running!
    - Starting...
    - Downloading file list...
    - Syncing "filename"
    - Up to date

Requires:
    dropbox-cli: command line tool

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD
"""

import shlex
import subprocess
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'Dropbox: {}'

    def dropbox(self, i3s_output_list, i3s_config):
        response = {'cached_until': time() + self.cache_timeout}

        lines = subprocess.check_output(
            shlex.split('dropbox-cli status')).decode('utf-8').split('\n')
        status = lines[0]
        full_text = self.format.format(str(status))
        response['full_text'] = full_text

        if status == "Dropbox isn't running!":
            response['color'] = i3s_config['color_bad']
        elif status == "Up to date":
            response['color'] = i3s_config['color_good']
        else:
            response['color'] = i3s_config['color_degraded']
        return response


if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.dropbox([], config))
        sleep(1)
