# -*- coding: utf-8 -*-
"""
Display if a process is running.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format: display format for process status (default '{icon}')
    full: if True, match against the full command line (default False)
    icon_off: display when the process is not running (default '■')
    icon_on: display when the process is running (default '●')
    msg_unavailable: display when no process name (default 'process_status: N/A')
    process: the process name to check if it is running (default None)

Format placeholders:
    {icon} display icon based on process status
    {process} display process name

Color options:
    color_bad: the process is not running or unavailable
    color_good: the process is running

@author obb, Moritz Lüdecke
"""

import os
import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{icon}'
    full = False
    icon_off = u'■'
    icon_on = u'●'
    msg_unavailable = 'process_status: N/A'
    process = None

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'format_running',
                    'new': 'icon_on',
                    'msg': 'obsolete parameter use `icon_on`',
                },
                {
                    'param': 'format_not_running',
                    'new': 'icon_off',
                    'msg': 'obsolete parameter use `icon_off`',
                },
            ],
        }

    def _get_text(self):
        fnull = open(os.devnull, 'w')
        pgrep = ["pgrep", self.process]

        if self.full:
            pgrep = ["pgrep", "-f", self.process]

        if subprocess.call(pgrep,
                           stdout=fnull, stderr=fnull) == 0:
            color = self.py3.COLOR_GOOD
            text = self.py3.safe_format(self.icon_on,
                                        {'process': self.process})
        else:
            color = self.py3.COLOR_BAD
            text = self.py3.safe_format(self.icon_off,
                                        {'process': self.process})

        return (color, text)

    def process_status(self):
        if self.process is None:
            color = self.py3.COLOR_BAD
            text = self.msg_unavailable
        else:
            (color, text) = self._get_text()

        return {
            'color': color,
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format,
                                              {'icon': text, 'process': self.process})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
