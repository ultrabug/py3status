# -*- coding: utf-8 -*-
"""
Display Yandex.Disk status.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 10)
    format: prefix text for the Yandex.Disk status
        (default 'Yandex.Disk: {status}')

Format of status string placeholders:
    {status} daemon status

Requires:
    yandex-disk: command line tool (link: https://disk.yandex.com/)

@author Vladimir Potapev (github:vpotapev)
@license BSD
"""

import shlex
import subprocess
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'Yandex.Disk: {status}'

    def yadisk(self, i3s_output_list, i3s_config):
        response = {'cached_until': time() + self.cache_timeout}

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
            response['color'] = i3s_config['color_bad']
        elif status == "Synchronization core status: idle":
            status = 'Idle'
            response['color'] = i3s_config['color_good']
        else:
            status = 'Busy'
            response['color'] = i3s_config['color_degraded']

        full_text = self.format.format(status=status)
        response['full_text'] = full_text
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
        print(x.yadisk([], config))
        sleep(1)
