#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Display currently playing song from Google Play Music Desktop Player.

Configuration parameters:
    - cache_timeout : how often we refresh this module in seconds (5s default)

Requires
    - gpmdp
    - gpmdp-remote

@author Aaron Fields https://twitter.com/spirotot
@license BSD
"""

# import your useful libs here
from time import time
from subprocess import check_output
import shlex


class Py3status:
    """
    """
    # available configuration parameters

    cache_timeout = 5
    format = u'♫ {info}'

    @staticmethod
    def run_cmd(cmd):
        return check_output(shlex.split('gpmdp-remote %s' % (cmd))).decode('utf-8').strip()

    def gpmdp(self, i3s_output_list, i3s_config):
        if self.run_cmd('status') == 'Paused':
            result = ''
        else:
            cmds = ['info', 'title', 'artist', 'album', 'status', 'current',
                    'status', 'time_total', 'time_current', 'album_art']
            data = {}
            for cmd in cmds:
                if '{%s}' % cmd in self.format:
                    data[cmd] = self.run_cmd(cmd)

            result = self.format.format(**data)

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': result
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
        print(x.gpmdp([], config))
        sleep(1)
