# -*- coding: utf-8 -*-

"""
Display insync status

Thanks to Iain Tatch <iain.tatch@gmail.com> for the script that this is based on.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 10)
    format: Display format to use (default '{status} {queued}')

Format placeholders:
    {status} Status of Insync
    {queued} Number of files queued

Color options:
    color_bad: Offline
    color_degraded: Default
    color_good: Synced

Requires:
    insync: command line tool

@author Joshua Pratt <jp10010101010000@gmail.com>
@license BSD
"""

from subprocess import check_output


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    format = '{status} {queued}'

    def check_insync(self):
        status = check_output(["insync", "get_status"]).decode().strip()
        color = self.py3.COLOR_DEGRADED
        if status == "OFFLINE":
            color = self.py3.COLOR_BAD
        if status == "SHARE":
            color = self.py3.COLOR_GOOD
            status = "INSYNC"

        queued = check_output(["insync", "get_sync_progress"]).decode()
        queued = [q for q in queued.split("\n") if q != '']
        if len(queued) > 0 and "queued" in queued[-1]:
            queued = queued[-1]
            queued = queued.split(" ")[0]
        else:
            queued = ""

        results = self.py3.safe_format(
            self.format, {'status': status, 'queued': queued}
        )

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
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
