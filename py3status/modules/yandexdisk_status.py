# -*- coding: utf-8 -*-
"""
Display Yandex.Disk status.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 10)
    format: prefix text for the Yandex.Disk status
        (default 'Yandex.Disk: {status}')

Format placeholders:
    {status} daemon status

Color options:
    color_bad: Not started
    color_degraded: Idle
    color_good: Busy

Requires:
    yandex-disk: command line tool (link: https://disk.yandex.com/)

@author Vladimir Potapev (github:vpotapev)
@license BSD
"""

import shlex
import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'Yandex.Disk: {status}'

    def yadisk(self):
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        raw_lines = b''
        try:
            raw_lines = subprocess.check_output(shlex.split('yandex-disk status'))
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raw_lines = e.output

        lines = raw_lines.decode('utf-8').split('\n')
        status = lines[0]

        if status == "Error: daemon not started":
            status = 'Not started'
            response['color'] = self.py3.COLOR_BAD
        elif status == "Synchronization core status: idle":
            status = 'Idle'
            response['color'] = self.py3.COLOR_GOOD
        else:
            status = 'Busy'
            response['color'] = self.py3.COLOR_DEGRADED

        full_text = self.py3.safe_format(self.format, {'status': status})
        response['full_text'] = full_text
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
