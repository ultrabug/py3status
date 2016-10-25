# -*- coding: utf-8 -*-
"""
Activate or deactivate DPMS and screen blanking.

This module allows activation and deactivation
of DPMS (Display Power Management Signaling)
by clicking on 'DPMS' in the status bar.

Configuration parameters:
    format_off: string to display when DPMS is disabled (default 'DPMS')
    format_on: string to display when DPMS is enabled (default 'DPMS')

Color options:
    color_on: when dpms is enabled, defaults to color_good
    color_off: when dpms is disabled, defaults to color_bad

@author Andre Doser <dosera AT tf.uni-freiburg.de>
"""

from os import system


class Py3status:
    """
    """
    # available configuration parameters
    format_off = "DPMS"
    format_on = "DPMS"

    def dpms(self):
        """
        Display a colorful state of DPMS.
        """

        self.run = system('xset -q | grep -iq "DPMS is enabled"') == 0

        return {
            'full_text': self.format_on if self.run else self.format_off,
            'color': self.py3.COLOR_ON or self.py3.COLOR_GOOD if self.run
            else self.py3.COLOR_OFF or self.py3.COLOR_BAD
        }

    def on_click(self, event):
        """
        Enable/Disable DPMS on left click.
        """
        if event['button'] == 1:
            if self.run:
                self.run = False
                system("xset -dpms;xset s off")
            else:
                self.run = True
                system("xset +dpms;xset s on")

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
