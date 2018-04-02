# -*- coding: utf-8 -*-
"""
Display number of pending updates for Arch Linux.

This will display a count of how many 'pacman' updates are waiting
to be installed and optionally a count of how many 'aur' updates are
also waiting.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 600)
    format: Display format to use
        (default 'UPD: {pacman}' or 'UPD: {pacman}/{aur}')
    hide_if_zero: Don't show on bar if True
        (default False)
    include_aur: Set to True to use 'cower' to check for AUR updates
        (default False)

Format placeholders:
    {aur} Number of pending aur updates
    {pacman} Number of pending pacman updates
    {total} Total updates pending

Requires:
    cower: Needed to display pending 'aur' updates

@author Iain Tatch <iain.tatch@gmail.com>
@license BSD

SAMPLE OUTPUT
{'full_text': 'UPD: 5'}

arch_updates_aur
{'full_text': 'UPD: 15/4'}
"""

import subprocess
import sys

FORMAT_PACMAN_ONLY = 'UPD: {pacman}'
FORMAT_PACMAN_AND_AUR = 'UPD: {pacman}/{aur}'
LINE_SEPARATOR = "\\n" if sys.version_info > (3, 0) else "\n"


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 600
    format = ''
    hide_if_zero = False
    include_aur = False

    def post_config_hook(self):
        if self.format == '':
            if not self.include_aur:
                self.format = FORMAT_PACMAN_ONLY
            else:
                self.format = FORMAT_PACMAN_AND_AUR
        self.include_aur = self.py3.format_contains(self.format, 'aur')
        self.include_pacman = self.py3.format_contains(self.format, 'pacman')
        if self.py3.format_contains(self.format, 'total'):
            self.include_aur = True
            self.include_pacman = True

        # check cower installed
        if self.include_aur and not self.py3.check_commands(['cower']):
            self.py3.notify_user('cower is not installed cannot check aur')
            self.include_aur = False

    def check_updates(self):
        pacman_updates = self._check_pacman_updates()
        aur_updates = self._check_aur_updates()
        if aur_updates == '?':
            total = pacman_updates
        else:
            total = pacman_updates + aur_updates

        if self.hide_if_zero and total == 0:
            full_text = ''
        else:
            full_text = self.py3.safe_format(
                self.format,
                {
                    'aur': aur_updates,
                    'pacman': pacman_updates,
                    'total': total,
                }
            )
        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text,
        }

    def _check_pacman_updates(self):
        """
        This method will use the 'checkupdates' command line utility
        to determine how many updates are waiting to be installed via
        'pacman -Syu'.
        """
        if not self.include_pacman:
            return 0
        pending_updates = str(subprocess.check_output(["checkupdates"]))
        return pending_updates.count(LINE_SEPARATOR)

    def _check_aur_updates(self):
        """
        This method will use the 'cower' command line utility
        to determine how many updates are waiting to be installed
        from the AUR.
        """
        # For reasons best known to its author, 'cower' returns a non-zero
        # status code upon successful execution, if there is any output.
        # See https://github.com/falconindy/cower/blob/master/cower.c#L2596
        if not self.include_aur:
            return '?'

        pending_updates = b""
        try:
            pending_updates = str(subprocess.check_output(["cower", "-u"]))
        except subprocess.CalledProcessError as cp_error:
            pending_updates = cp_error.output
        except:
            pending_updates = '?'
        return str(pending_updates).count(LINE_SEPARATOR)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
