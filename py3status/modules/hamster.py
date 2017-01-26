# -*- coding: utf-8 -*-
"""
Display time tracking activities from Hamster.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    format: see placeholders below (default '{current}')

Format placeholders:
    {current} current activity

Requires:
    hamster:

@author Aaron Fields (spirotot [at] gmail.com)
@license BSD
"""
import shlex
from subprocess import check_output


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{current}'

    def hamster(self):
        cur_task = check_output(shlex.split('hamster current'))
        cur_task = cur_task.decode('ascii', 'ignore').strip()
        if cur_task != 'No activity':
            cur_task = cur_task.split()
            time_elapsed = cur_task[-1]
            cur_task = cur_task[2:-1]
            cur_task = "%s (%s)" % (" ".join(cur_task), time_elapsed)

        response = {}
        response['cached_until'] = self.py3.time_in(self.cache_timeout)
        response['full_text'] = self.py3.safe_format(self.format,
                                                     {'current': cur_task})
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
