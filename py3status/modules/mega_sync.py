# -*- coding: utf-8 -*-
"""
Display status of MEGA sync.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default "MEGA: {SyncState_0}")

Format placeholders:
    <column>_<ID> where <column> and <ID> are returned by 'mega-sync' command.

Requires:
    MEGAcmd: command-line interface for MEGA

@author Maxim Baz (https://github.com/maximbaz)
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'MEGA: Synced'}
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
        try:
            output = self.py3.command_output("mega-sync").splitlines()
        except self.py3.CommandError as e:
            error = e.output or e.error
            self.py3.error("error: " + error)

        format_data = {}
        columns = output[0].split()
        for line in output[1:]:
            cells = dict(zip(columns, line.split()))
            suffixed_cells = {
                key + "_" + cells["ID"]: value for key, value in cells.items()
            }
            format_data.update(suffixed_cells)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, format_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
