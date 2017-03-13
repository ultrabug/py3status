# -*- coding: utf-8 -*-
"""
Display number of pending updates for Arch Linux.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 600)
    format: display format for this module
        *(default '[\?if=pacman&if=!aur PAC: {pacman}][\?if=!pacman&if=aur AUR: {aur}]
        [\?if=pacman&if=aur UPD: {pacman}/{aur}]')*

Format placeholders:
    {aur} Number of pending AUR updates
    {pacman} Number of pending updates
    {total} Total number of pending updates

Requires:
    checkupdates: safely print a list of pending updates
        (usually found in 'pacman' package)
    cower: a simple AUR downloader

@author Iain Tatch <iain.tatch@gmail.com>
@license BSD
"""

STRING_UNAVAILABLE = 'disabled'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 600
    format = '[\?if=pacman&if=!aur PAC: {pacman}][\?if=!pacman&if=aur AUR: {aur}]' + \
        '[\?if=pacman&if=aur UPD: {pacman}/{aur}]'

    class Meta:
        deprecated = {
            'remove': [
                {
                    'param': 'include_aur',
                    'msg': 'obsolete, customize format',
                },
            ],
        }

    def post_config_hook(self):
        if (self.py3.format_contains(self.format, 'pacman') and
                self.py3.check_commands('checkupdates')):
            self._pacman = True
        else:
            self._pacman = False

        if (self.py3.format_contains(self.format, 'aur') and
                self.py3.check_commands('cower') and self.include_aur):
            self._aur = True
        else:
            self._aur = False

        if not self._pacman and not self._aur:
            raise Exception(STRING_UNAVAILABLE, self.py3.CACHE_FOREVER)

    def arch_updates(self):
        """
        Display a count of pending updates and a count of pending AUR updates.
        """
        pacman = self._check_pacman_updates()
        aur = self._check_aur_updates()
        total = pacman + aur

        full_text = self.py3.safe_format(
            self.format, {'pacman': pacman, 'aur': aur, 'total': total}
        )

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text,
        }

    def _check_pacman_updates(self):
        """
        checkupdates -- Safely print a list of pending updates
            (usually found in 'pacman' package)
        """
        if self._pacman:
            return len(self.py3.command_output('checkupdates').splitlines())
        else:
            return 0

    def _check_aur_updates(self):
        """
        cower -bu -- Safely print a list of pending AUR updates

        -b, --brief
            Show output in a more script friendly format. Use this if you're wrapping cower
            for some sort of automation.

        -u, --update
            Check foreign packages for updates in the AUR. Without any arguments,
            all manually installed packages will be checked. cower will exit with a non-zero
            status if and only if updates are available.
        """
        # if self.check_aur:
        #     try:
        #         return len(subprocess.check_output(['cower', '-bu']).splitlines())
        #     except subprocess.CalledProcessError as e:
        #         return len(e.output.splitlines())
        #     except:
        #         return 0
        # else:
        #     return 0

        # GUESSWORK: NEW PY3 CODE W/ EXCEPTION TO TRY.
        if self._aur:
            try:
                return len(self.py3.command_output(['cower', '-bu']).splitlines())
            except self.py3.CommandError as e:
                return len(e.splitlines())
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
