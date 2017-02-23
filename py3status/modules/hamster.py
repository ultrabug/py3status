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

SAMPLE OUTPUT
{'full_text': 'Watering flowers@Day-to-day (00:03)'}

inactive
{'full_text': 'No activity'}
"""


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{current}'

    def hamster(self):
        cur_task = self.py3.command_output('hamster current').strip()
        if cur_task != 'No activity':
            cur_task = cur_task.split()
            time_elapsed = cur_task[-1]
            cur_task = cur_task[2:-1]
            cur_task = u"%s (%s)" % (" ".join(cur_task), time_elapsed)

        return {'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format, {'current': cur_task})}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
