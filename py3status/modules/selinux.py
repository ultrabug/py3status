# -*- coding: utf-8 -*-
"""
Display the current selinux state.

This module displays the current state of selinux on your machine: Enforcing
(good), Permissive (bad), or Disabled (bad).

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (10s default)
    format: see placeholders below, default is 'selinux: {state}'

Format of status string placeholders:
    {state} the current selinux state

Requires:
    libselinux-python:
        or
    libselinux-python3: (optional for python3 support)

@author bstinsonmhk
@license BSD
"""

import selinux
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'selinux: {state}'

    def selinux_status(self, i3s_output_list, i3s_config):
        try:
            if selinux.security_getenforce():
                selinuxstring = 'enforcing'
                color = 'color_good'
            else:
                selinuxstring = 'permissive'
                color = 'color_bad'
        except OSError:
            selinuxstring = 'disabled'
            color = 'color_bad'

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': self.format.format(state=selinuxstring),
            'color': i3s_config[color]
        }

        return response


if __name__ == '__main__':
    from time import sleep

    x = Py3status()

    config = {
        'color_good': '#00FF00',
        'color_degraded': '#FFFF00',
        'color_bad': '#FF0000',
    }

    while True:
        print(x.selinux_status([], config))
        sleep(1)
