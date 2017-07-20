# -*- coding: utf-8 -*-
"""
Display number of pending updates for Ubuntu based Distros.

Thanks to Iain Tatch <iain.tatch@gmail.com> for the script that this is based on.

This will display a count of how many 'apt' updates are waiting to be installed.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 600)
    format: Display format to use
        (default 'UPD: {apt}')
    no_updates: Display format to use if there are no updates

Format placeholders:
    {apt} Number of pending apt updates

Requires:
    apt: Needed to display pending 'apt' updates

@author Joshua Pratt <jp10010101010000@gmail.com>
@license BSD

SAMPLE OUTPUT
{'full_text': 'UPD: 5'}
"""

import subprocess
import sys

FORMAT = 'UPD: {apt}'
NO_UPDATES = 'UPD'
LINE_SEPARATOR = "\\n" if sys.version_info > (3, 0) else "\n"


class Py3status:
    # available configuration parameters
    cache_timeout = 600
    format = FORMAT
    no_updates = NO_UPDATES

    def post_config_hook(self):
        self.include_apt = self.py3.format_contains(self.format, 'apt')

    def check_updates(self):
        apt_updates = self._check_apt_updates()

        color = self.py3.COLOR_DEGRADED
        if apt_updates == 0:
            color = self.py3.COLOR_GOOD
            full_text = self.no_updates
        else:
            full_text = self.py3.safe_format(
                self.include_apt,
                {
                    'apt': apt_updates
                }
            )
        return {
            'color': color,
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text,
        }

    def _check_apt_updates(self):
        """
        This method will use the 'checkupdates' command line utility
        to determine how many updates are waiting to be installed via
        'apt list --upgradeable'.
        """
        pending_updates = str(subprocess.check_output(["apt", "list", "--upgradeable"]))
        pending_updates = pending_updates.split(LINE_SEPARATOR)
        pending_updates = pending_updates[1:-1]
        return len(pending_updates)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
