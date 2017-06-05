# -*- coding: utf-8 -*-
"""
Monitor CapsLock, NumLock, and ScrLock keys

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    format: display format for this module (default '{caps} {num} {scr}')
    icon_caps_off: show when Capitals Lock is off (default 'CAPS')
    icon_caps_on: show when Capitals Lock is on (default 'CAPS')
    icon_num_off: show when Numeric Lock is off (default 'NUM')
    icon_num_on: show when Numeric Lock is on (default 'NUM')
    icon_scr_off: show when Scroll Lock is off (default 'SCR')
    icon_scr_on: show when Scroll Lock is on (default 'SCR')

Color options:
    color_good: Lock on
    color_bad: Lock off

@author lasers

SAMPLE OUTPUT
[
    {'color': '#00FF00', 'full_text': 'CAPS '},
    {'color': '#00FF00', 'full_text': 'NUM '},
    {'color': '#FF0000', 'full_text': 'SCR'},
]

no_locks
[
    {'color': '#FF0000', 'full_text': 'CAPS '},
    {'color': '#FF0000', 'full_text': 'NUM '},
    {'color': '#FF0000', 'full_text': 'SCR'},
]
"""


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 1
    format = '{caps} {num} {scr}'
    icon_caps_off = 'CAPS'
    icon_caps_on = 'CAPS'
    icon_num_off = 'NUM'
    icon_num_on = 'NUM'
    icon_scr_off = 'SCR'
    icon_scr_on = 'SCR'

    def post_config_hook(self):
        self.caps = self.py3.format_contains(self.format, 'caps')
        self.num = self.py3.format_contains(self.format, 'num')
        self.scr = self.py3.format_contains(self.format, 'scr')

    def keyboard_locks(self):
        out = self.py3.command_output('xset -q')

        if self.caps:
            if 'on' in out.split('Caps Lock:')[1][0:6]:
                caps_color = self.py3.COLOR_GOOD
                caps = self.icon_caps_on
            else:
                caps_color = self.py3.COLOR_BAD
                caps = self.icon_caps_off
            if caps:
                caps = self.py3.composite_create(
                    {'full_text': caps, 'color': caps_color})

        if self.num:
            if 'on' in out.split('Num Lock:')[1][0:6]:
                num_color = self.py3.COLOR_GOOD
                num = self.icon_num_on
            else:
                num_color = self.py3.COLOR_BAD
                num = self.icon_num_off
            if num:
                num = self.py3.composite_create(
                    {'full_text': num, 'color': num_color})

        if self.scr:
            if 'on' in out.split('Scroll Lock:')[1][0:6]:
                scr_color = self.py3.COLOR_GOOD
                scr = self.icon_scr_on
            else:
                scr_color = self.py3.COLOR_BAD
                scr = self.icon_scr_off
            if scr:
                scr = self.py3.composite_create(
                    {'full_text': scr, 'color': scr_color})

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {'caps': caps, 'num': num, 'scr': scr})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
