# -*- coding: utf-8 -*-
"""
Display status of MEGA sync.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default "MEGA: {SyncState_0}")

Format placeholders:
    <column>_<ID> where <column> is the names returned by 'mega-sync' command.
    For example: SyncState_0, LOCALPATH_3, ActState_7

Requires:
    MEGAcmd: command-line interface for MEGA

@author Maxim Baz (https://github.com/maximbaz)
@license BSD

SAMPLE OUTPUT
{'full_text': 'MEGA: Synced'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "MEGA: {SyncState_0}"

    def post_config_hook(self):
        if not self.py3.check_commands("mega-sync"):
            raise Exception("MEGAcmd is not installed")

    def mega_sync(self):
        output = self.py3.command_output("mega-sync").splitlines()
        columns = output[0].split()
        megasync_data = {}
        for line in output[1:]:
            cells = dict(zip(columns, line.split()))
            megasync_data.update(
                {key + "_" + cells["ID"]: value for key, value in cells.items()}
            )

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, megasync_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
