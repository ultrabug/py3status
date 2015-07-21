# -*- coding: utf-8 -*-
"""
Activate or deactivate DPMS and screen blanking.

This module allows activation and deactivation
of DPMS (Display Power Management Signaling)
by clicking on 'DPMS' in the status bar.

Configuration parameters:
    - format_off: string to display when DPMS is enabled
    - format_on: string to display when DPMS is disabled

@author Andre Doser <dosera AT tf.uni-freiburg.de>
"""

from os import system


class Py3status:
    """
    """
    # available configuration parameters
    format_off = "DPMS"
    format_on = "DPMS"

    def dpms(self, i3s_output_list, i3s_config):
        """
        Display a colorful state of DPMS.
        """

        self.run = system('xset -q | grep -iq "DPMS is enabled"') == 0

        response = {
            'full_text': self.format_on if self.run else self.format_off,
            'color': i3s_config['color_good'] if self.run else i3s_config['color_bad']
        }

        return response

    def on_click(self, i3s_output_list, i3s_config, event):
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
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_good': '#00FF00',
    }

    while True:
        print(x.dpms([], config))
        sleep(1)
