# -*- coding: utf-8 -*-
"""
Display Insync status

Thanks to Iain Tatch <iain.tatch@gmail.com> for the script that this is based on.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{status} {queued}')
    string_offline: show when Insync is offline (default 'OFFLINE')
    string_paused: show when Insync is paused (default 'PAUSED')
    string_share: show when Insync is sharing (default 'SHARE')
    string_syncing: show when Insync is syncing (default 'SYNCING')
    string_unavailable: show when unavailable (default "Insync: isn't installed")

Format placeholders:
    {status} Insync status
    {queued} Number of files queued

Color options:
    color_bad: Offline
    color_degraded: Default
    color_good: Synced

Requires:
    insync: an unofficial Google Drive client with support for various desktops


@author Joshua Pratt <jp10010101010000@gmail.com>
@license BSD
"""


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    format = '{status} {queued}'
    string_offline = 'OFFLINE'
    string_paused = 'PAUSED'
    string_share = 'SHARE'
    string_syncing = 'SYNCING'
    string_unavailable = "Insync: isn't installed"

    def insync(self):
        if not self.py3.check_commands(["insync"]):
            return {'cached_until': self.py3.CACHE_FOREVER,
                    'color': self.py3.COLOR_BAD,
                    'full_text': self.string_unavailable}

        # get sync progress
        queued = self.py3.command_output(["insync", "get_sync_progress"]).splitlines()
        queued = [q for q in queued if q != '']
        if len(queued) > 0 and "queued" in queued[-1]:
            queued = queued[-1]
            queued = queued.split(" ")[0]
        else:
            queued = ''

        # get status
        status = self.py3.command_output(["insync", "get_status"]).strip()
        color = self.py3.COLOR_DEGRADED
        if status == "SHARE":
            color = self.py3.COLOR_GOOD
            status = self.string_share
        elif status == "OFFLINE":
            color = self.py3.COLOR_BAD
            status = self.string_offline
        elif status == "PAUSED":
            status = self.string_paused
        elif status == "SYNCING":
            status = self.string_syncing

        return {
            'color': color,
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {'status': status, 'queued': queued})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
