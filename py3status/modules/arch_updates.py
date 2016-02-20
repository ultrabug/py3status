# -*- coding: utf-8 -*-

"""
Displays the number of package updates pending for an Arch Linux installation.

This will display a count of how many 'pacman' updates are waiting
to be installed and optionally a count of how many 'aur' updates are
also waiting.

To display pending 'aur' updates you need to have installed 'cower'.

Configuration parameters:
    - cache_timeout : how often we refresh this module in seconds (default 600)
    - include_aur : set to 0 to use 'cower' to check for AUR updates (default 0)

@author Iain Tatch <iain.tatch@gmail.com>
@license BSD
"""

from time import time
import sh


class Py3status:
    # available configuration parameters
    cache_timeout = 600
    include_aur = 0


    def check_updates(self, i3s_output_list, i3s_config):
        pacman_updates = self._check_pacman_updates()
        if self.include_aur:
            aur_updates = self._check_aur_updates()
            results = "{0}/{1}".format(pacman_updates, aur_updates)
        else:
            results = str(pacman_updates)

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': 'UPD: ' + results
        }
        return response

    def _check_pacman_updates(self):
        """
        This method will use the 'checkupdates' command line utility
        to determine how many updates are waiting to be installed via
        'pacman -Syu'.
        """
        pending_updates = sh.checkupdates()
        return len(pending_updates)

    def _check_aur_updates(self):
        """
        This method will use the 'cower' command line utility
        to determine how many updates are waiting to be installed
        from the AUR.
        """
        pending_updates = sh.cower('-u')
        return len(pending_updates)

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
