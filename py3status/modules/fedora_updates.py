# -*- coding: utf-8 -*-
"""
The number of package updates pending for a Fedora Linux installation.

This will display a count of how many `dnf` updates are waiting
to be installed.
Additionally check if any update security notices.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 600)
    color_bad: Color when security notice
        (default global color_bad)
    color_degraded: Color when upgrade available
        (default global color_degraded)
    color_good: Color when no upgrades needed
        (default global color_good)
    format: Display format to use
        (default 'DNF: {updates}')

Format status string parameters:
    {updates} number of pending dnf updates

@author Toby Dacre
@license BSD
"""

from time import time
import subprocess
import re


class Py3status:
    # available configuration parameters
    cache_timeout = 600
    color_bad = None
    color_degraded = None
    color_good = None
    format = 'DNF: {updates}'

    def __init__(self):
        self._reg_ex_sec = re.compile('\d+(?=\s+Security)')
        self._reg_ex_pkg = re.compile(b'^\S+\.', re.M)
        self._first = True
        self._updates = None
        self._security_notice = False

    def check_updates(self, i3s_output_list, i3s_config):
        if self._first:
            self._first = False
            response = {
                'cached_until': time(),
                'full_text': self.format.format(updates='?')
            }
            return response

        output, error = subprocess.Popen(
            ['dnf', 'check-update'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate()

        updates = len(self._reg_ex_pkg.findall(output))

        if updates == 0:
            color = self.color_good or i3s_config['color_good']
            self._updates = 0
            self._security_notice = False
        else:
            if not self._security_notice and self._updates != updates:
                output, error = subprocess.Popen(
                    ['dnf', 'updateinfo'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE).communicate()
                notices = str(output)
                self._security_notice = len(self._reg_ex_sec.findall(notices))
                self._updates = updates
            if self._security_notice:
                color = self.color_bad or i3s_config['color_bad']
            else:
                color = self.color_degraded or i3s_config['color_degraded']

        response = {
            'cached_until': time() + self.cache_timeout,
            'color': color,
            'full_text': self.format.format(updates=updates)
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
        print(x.check_updates([], config))
        sleep(1)
