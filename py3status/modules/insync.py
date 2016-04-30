# -*- coding: utf-8 -*-

"""
Gets the current insync status

Configuration parameters:
    format: Display format to use *(default
        '{status}'
        )*

Format status string parameters:
    {status} Status of Insync
    {files} Number of pending syncing files

@author Joshua Pratt <jp10010101010000@gmail.com>
Thanks to @author Iain Tatch <iain.tatch@gmail.com> for the script that this is based on
@license BSD
"""

from time import time
import subprocess
import sys


class Py3status:
    # available configuration parameters
    cache_timeout = 1
    format = ''
    _format_default = '{status}'
    _line_separator = "\\n" if sys.version_info > (3, 0) else "\n"

    if format == '':
        format = _format_default

    def check_insync(self, i3s_output_list, i3s_config):
        status, color = self._check_insync_status(i3s_config)
        results = self.format.format(status=str(status))

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': results,
            'color' : color
        }
        return response

    def _check_insync_status(self, config):
        """
        """

        status = str(subprocess.check_output(["/usr/bin/insync", "get_status"]))
        if len(status) > 5:
            status = status[2:-3]
        #print(status)
        color = config.get('color_degraded', '')
        if status == "OFFLINE":
            color = config.get('color_bad', '')
        if status == "SHARE":
            color = config.get('color_good', '')
            status = "INSYNC"
        return status, color

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
        print(x.check_insync([], config))
        sleep(1)
