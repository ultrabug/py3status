# -*- coding: utf-8 -*-

"""
Displays the number of package updates pending for an Arch Linux installation.
This will display a count of how many 'pacman' updates are waiting
to be installed and optionally a count of how many 'aur' updates are
also waiting.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 600)
    include_aur: Set to 0 to use 'cower' to check for AUR updates (default 0)
    format: Display format to use *(default
        'UPD: {pacman}' or 'UPD: {pacman}/{aur}'
        )*

Format status string parameters:
    {aur} Number of pending aur updates
    {pacman} Number of pending pacman updates

Requires:
    cower: Needed to display pending 'aur' updates

@author Iain Tatch <iain.tatch@gmail.com>
@license BSD
"""

from time import time
import subprocess
import sys


class Py3status:
    # available configuration parameters
    cache_timeout = 600
    include_aur = 0
    format = ''

    _format_pacman_only = 'UPD: {pacman}'
    _format_pacman_and_aur = 'UPD: {pacman}/{aur}'
    _line_separator = "\\n" if sys.version_info > (3, 0) else "\n"

    if format == '':
        if include_aur == 0:
            format = _format_pacman_only
        else:
            format = _format_pacman_and_aur

    def check_updates(self, i3s_output_list, i3s_config):
        pacman_updates = self._check_pacman_updates()
        if self.include_aur:
            aur_updates = self._check_aur_updates()
            results = self.format.format(pacman=pacman_updates,
                                         aur=aur_updates)
        else:
            results = self.format.format(pacman=str(pacman_updates))

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': results
        }
        return response

    def _check_pacman_updates(self):
        """
        This method will use the 'checkupdates' command line utility
        to determine how many updates are waiting to be installed via
        'pacman -Syu'.
        """
        pending_updates = str(subprocess.check_output(["checkupdates"]))
        return pending_updates.count(self._line_separator)

    def _check_aur_updates(self):
        """
        This method will use the 'cower' command line utility
        to determine how many updates are waiting to be installed
        from the AUR.
        """
        # For reasons best known to its author, 'cower' returns a non-zero
        # status code upon successful execution, if there is any output.
        # See https://github.com/falconindy/cower/blob/master/cower.c#L2596
        pending_updates = b""
        try:
            pending_updates = str(subprocess.check_output(["cower", "-bu"]))
        except subprocess.CalledProcessError as cp_error:
            pending_updates = cp_error.output
        except:
            pending_updates = '?'

        return str(pending_updates).count(self._line_separator)

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
        print(x.check_updates([], config))
        sleep(1)
