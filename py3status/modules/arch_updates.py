# -*- coding: utf-8 -*-
"""
Display number of pending updates for Arch Linux.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 600)
    check_aur: check aur for pending updates (default None)
    check_pacman: check pacman for pending updates (default None)
    format: display format for this module (default '{updates}')
    format_aur: (default 'UPD: {aur}')
    format_full: (default 'UPD: {pacman}/{aur}')
    format_pacman: (default 'UPD: {pacman}')

Format placeholders:
    {aur} Number of pending AUR updates
    {pacman} Number of pending Pacman updates
    {total} Number of pending total updates

Requires:
    cower: A simple AUR agent with a pretentious name

@author Iain Tatch <iain.tatch@gmail.com>
@license BSD
"""
import subprocess

STRING_UNAVAILABLE = 'arch_updates: N/A'


class Py3status:
    # available configuration parameters
    cache_timeout = 600
    check_aur = None
    check_pacman = None
    format = '{updates}'
    format_aur = 'UPD: {aur}'
    format_full = 'UPD: {pacman}/{aur}'
    format_pacman = 'UPD: {pacman}'

    def post_config_hook(self):
        if self.check_pacman is None:
            self.check_pacman = self.py3.check_commands('pacman')
        if self.check_aur is None:
            self.check_aur = self.py3.check_commands('cower')

        if not self.check_pacman and not self.check_aur:
            return {
                'cached_until': self.py3.CACHE_FOREVER,
                'full_text': STRING_UNAVAILABLE,
                'color': self.py3.COLOR_BAD
            }

    def arch_updates(self):
        pacman = self._check_pacman()
        aur = self._check_aur()
        total = pacman + aur

        if pacman > 0 and aur == 0 and self.check_pacman:
            self.format = self.format_pacman
        elif pacman == 0 and aur > 0 and self.check_aur:
            self.format = self.format_aur
        else:
            self.format = self.format_full

        arch_updates = self.py3.safe_format(
            self.format, {'pacman': pacman, 'aur': aur, 'total': total}
        )

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': arch_updates
        }

    def _check_pacman(self):
        if self.check_pacman:
            return len(self.py3.command_output('checkupdates').splitlines())
        else:
            return 0

    def _check_aur(self):
        # For reasons best known to its author, 'cower' returns a non-zero
        # status code upon successful execution, if there is any output.
        if self.check_aur:
            try:
                return len(subprocess.check_output(['cower', '-bu']).splitlines())
            except subprocess.CalledProcessError as e:
                return len(e.output.splitlines())
            except:
                return 0
        else:
            return 0


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
