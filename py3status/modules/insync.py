# -*- coding: utf-8 -*-
"""
Display Insync status.

Thanks to Iain Tatch <iain.tatch@gmail.com> for the script that this is based on.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{status} {queued}')
    status_offline: show when Insync is offline (default 'OFFLINE')
    status_paused: show when Insync is paused (default 'PAUSED')
    status_share: show when Insync is sharing (default 'SHARE')
    status_synced: show when Insync has finished syncing (default 'SYNCED')
    status_syncing: show when Insync is syncing (default 'SYNCING')

Format placeholders:
    {status} Insync status
    {queued} Number of files queued

Color options:
    color_bad: Offline
    color_degraded: Default (e.g. Paused/Syncing)
    color_good: Synced

Requires:
    insync: an unofficial Google Drive client with support for various desktops

@author Joshua Pratt <jp10010101010000@gmail.com>
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'INSYNC 3'}

busy
{'color': '#FFFF00', 'full_text': u'PAUSED 3'}

offline
{'color': '#FF0000', 'full_text': u'OFFLINE 3'}
"""

STRING_ERROR = "Insync: isn't running"
STRING_NOT_INSTALLED = "not installed"
STRING_UNEXPECTED = "Insync: N/A"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{status} {queued}"
    status_offline = "OFFLINE"
    status_paused = "PAUSED"
    status_share = "SHARE"
    status_synced = "SYNCED"
    status_syncing = "SYNCING"

    def post_config_hook(self):
        if not self.py3.check_commands("insync"):
            raise Exception(STRING_NOT_INSTALLED)

    def insync(self):
        # sync progress
        try:
            queued = self.py3.command_output(
                ["insync", "get_sync_progress"]
            ).splitlines()
        except Exception:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "color": self.py3.COLOR_ERROR or self.py3.COLOR_BAD,
                "full_text": STRING_UNEXPECTED,
            }
        queued = [q for q in queued if q != ""]
        if len(queued) > 0 and "queued" in queued[-1]:
            queued = queued[-1]
            queued = queued.split(" ")[0]
        else:
            queued = ""

        # status
        try:
            status = self.py3.command_output(["insync", "get_status"]).strip()
        except Exception:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "color": self.py3.COLOR_ERROR or self.py3.COLOR_BAD,
                "full_text": STRING_UNEXPECTED,
            }

        color = self.py3.COLOR_DEGRADED
        format = self.format
        if status == "Insync doesn't seem to be running. Start it first.":
            self.py3.error(STRING_ERROR)
        elif status == "OFFLINE":
            color = self.py3.COLOR_BAD
            status = self.status_offline
        elif status == "SYNCED":
            color = self.py3.COLOR_GOOD
            status = self.status_synced
        elif status == "SHARE":
            status = self.status_share
        elif status == "PAUSED":
            status = self.status_paused
        elif status == "SYNCING":
            status = self.status_syncing

        return {
            "color": color,
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                format, {"status": status, "queued": queued}
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
