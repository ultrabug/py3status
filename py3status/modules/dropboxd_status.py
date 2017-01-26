# -*- coding: utf-8 -*-
"""
Display status of Dropbox daemon.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    format: prefix text for the dropbox status (default 'Dropbox: {}')

Valid status values include:
    - Dropbox isn't running!
    - Starting...
    - Downloading file list...
    - Syncing "filename"
    - Up to date

Color options:
    color_bad: Dropbox is unavailable
    color_degraded: All other statuses
    color_good: Dropbox up-to-date

Requires:
    dropbox-cli: command line tool

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD
"""

import shlex
import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'Dropbox: {}'

    def dropbox(self):
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        lines = subprocess.check_output(
            shlex.split('dropbox-cli status')).decode('utf-8').split('\n')
        status = lines[0]
        full_text = self.format.format(str(status))
        response['full_text'] = full_text

        if status == "Dropbox isn't running!":
            response['color'] = self.py3.COLOR_BAD
        elif status == "Up to date":
            response['color'] = self.py3.COLOR_GOOD
        else:
            response['color'] = self.py3.COLOR_DEGRADED
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
