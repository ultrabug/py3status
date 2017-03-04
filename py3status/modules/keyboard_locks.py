# -*- coding: utf-8 -*-
"""
Monitor CapsLock, NumLock, and ScrLock keys

NumLock: Allows the user to type numbers by pressing the keys on the number pad,
rather than having them act as up, down, left, right, page up, end, and so forth.

CapsLock: When enabled, letters the user types will be in uppercase by default
rather than lowercase.

ScrLock: In some applications, such as spreadsheets, the lock mode is used to
change the behavior of the cursor keys to scroll the document instead of the cursor.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    icon_capslock_off: show when Caps Lock is off (default 'CAP')
    icon_capslock_on: show when Caps Lock is on (default 'CAP')
    icon_numlock_off: show when Num Lock is off (default 'NUM')
    icon_numlock_on: show when Num Lock is off (default 'NUM')
    icon_scrlock_off: show when Scroll Lock is off (default 'SCR')
    icon_scrlock_on: show when Scroll Lock is on (default 'SCR')

Color options:
    color_good: Lock on
    color_bad: Lock off

@author lasers
"""


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 1
    icon_capslock_off = "CAP"
    icon_capslock_on = "CAP"
    icon_numlock_off = "NUM"
    icon_numlock_on = "NUM"
    icon_scrlock_off = "SCR"
    icon_scrlock_on = "SCR"

    def keyboard_lock(self):
        out = self.py3.command_output('xset -q')

        capslock_color = self.py3.COLOR_BAD
        capslock_icon = self.icon_capslock_off
        numlock_color = self.py3.COLOR_BAD
        numlock_icon = self.icon_numlock_off
        scrlock_color = self.py3.COLOR_BAD
        scrlock_icon = self.icon_scrlock_off

        if 'on' in out.split("Caps Lock:")[1][0:6]:
            capslock_color = self.py3.COLOR_GOOD
            capslock_icon = self.icon_capslock_on

        if 'on' in out.split("Num Lock:")[1][0:6]:
            numlock_color = self.py3.COLOR_GOOD
            numlock_icon = self.icon_numlock_on

        if 'on' in out.split("Scroll Lock:")[1][0:6]:
            scrlock_color = self.py3.COLOR_GOOD
            scrlock_icon = self.icon_scrlock_on

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'composite': [
                {
                    'color': capslock_color,
                    'full_text': capslock_icon,
                },
                {
                    'full_text': ' '
                },
                {
                    'color': numlock_color,
                    'full_text': numlock_icon,
                },
                {
                    'full_text': ' '
                },
                {
                    'color': scrlock_color,
                    'full_text': scrlock_icon,
                },
            ]
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
