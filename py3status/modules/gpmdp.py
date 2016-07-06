#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Display currently playing song from Google Play Music Desktop Player.
Configuration parameters:
    - cache_timeout : how often we refresh this module in seconds (5s default)
    - format        : Insert the output of various gpmdp-remote commands (see gpmdp-remote help) into the format string.

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
    # available configuration parameters

    cache_timeout = 5 
    format = '{info}'

    def gpmdp(self, i3s_output_list, i3s_config):
        result = u'♫ ' + self.format
        #command = 'gpmdp-remote info'
        #result = u'♫ ' + check_output(shlex.split(command)).decode('ascii','ignore').strip()
        #split = result.split()

        if check_output(shlex.split('gpmdp-remote status')).decode('ascii', 'ignore').strip() == 'Paused':
            result = ''
        else:
            cmds = ['info','title','artist','album','status','current','status','time_total','time_current','album_art']

            for cmd in cmds:
                if str('{' + cmd + '}') in result:
                    result = result.replace(str('{' + cmd + '}'), check_output(shlex.split('gpmdp-remote %s' % (cmd))).decode('ascii', 'ignore').strip())

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
