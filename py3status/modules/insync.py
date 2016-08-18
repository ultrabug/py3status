# -*- coding: utf-8 -*-

"""
Get current insync status

Thanks to Iain Tatch <iain.tatch@gmail.com> for the script that this is based on.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 10)
    format: Display format to use (default '{status} {queued}')

Format status string parameters:
    {status} Status of Insync
    {queued} Number of files queued

Requires:
    insync: command line tool

@author Joshua Pratt <jp10010101010000@gmail.com>
@license BSD
"""

from time import time
from subprocess import check_output


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    format = '{status} {queued}'

    def check_insync(self, i3s_output_list, i3s_config):
        status = check_output(["insync", "get_status"]).decode().strip()
        color = i3s_config.get('color_degraded', '')
        if status == "OFFLINE":
            color = i3s_config.get('color_bad', '')
        if status == "SHARE":
            color = i3s_config.get('color_good', '')
            status = "INSYNC"

        queued = check_output(["insync", "get_sync_progress"]).decode()
        queued = [q for q in queued.split("\n") if q != '']
        if len(queued) > 0 and "queued" in queued[-1]:
            queued = queued[-1]
            queued = queued.split(" ")[0]
        else:
            queued = ""

        results = self.format.format(status=status, queued=queued)

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': results,
            'color': color
        }
        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
