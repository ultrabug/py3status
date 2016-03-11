# -*- coding: utf-8 -*-
"""
Display current tasks from project Hamster.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (5s default)
    format: see placeholders below

Format of status string placeholders:
    {current} hamster current

Requires:
    hamster:

@author Aaron Fields (spirotot [at] gmail.com)
@license BSD
"""
import shlex
from subprocess import check_output
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{current}'

    def hamster(self, i3s_output_list, i3s_config):
        cur_task = check_output(shlex.split('hamster current'))
        cur_task = cur_task.decode('ascii', 'ignore').strip()
        if cur_task != 'No activity':
            cur_task = cur_task.split()
            time_elapsed = cur_task[-1]
            cur_task = cur_task[2:-1]
            cur_task = "%s (%s)" % (" ".join(cur_task), time_elapsed)

        response = {}
        response['cached_until'] = time() + self.cache_timeout
        response['full_text'] = self.format.format(current=cur_task)
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
        print(x.hamster([], config)['full_text'])
        sleep(1)
