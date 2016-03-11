# -*- coding: utf-8 -*-
"""
Display the X selection.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default is at every py3status configured interval)
    command: the xsel command to run (default 'xsel')
    max_size: stip the selection to this value (default 15)
    symmetric: show the beginning and the end of the selection string
        with respect to configured max_size.

Requires:
    xsel: command line tool

@author Sublim3 umbsublime@gamil.com
@license BSD
"""

import shlex

from time import time
from subprocess import check_output


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 0.5
    command = 'xsel'
    max_size = 15
    symmetric = True
    color = "#0066FF"

    def xsel(self, i3s_output_list, i3s_config):
        """
        Display the content of xsel.
        """
        current_value = check_output(shlex.split(self.command))
        if len(current_value) >= self.max_size:
            if self.symmetric is True:
                split = int(self.max_size / 2) - 1
                current_value = current_value[:split].decode(
                    'utf-8') + '..' + current_value[-split:].decode('utf-8')
            else:
                current_value = current_value[:self.max_size]
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': current_value,
            'color': self.color
        }
        return response


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.xsel([], config))
        sleep(1)
