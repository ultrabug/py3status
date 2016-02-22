# -*- coding: utf-8 -*-
"""
Activate or deactivate DPMS and screen blanking.

This module allows activation and deactivation
of DPMS (Display Power Management Signaling)
by clicking on 'DPMS' in the status bar.

Configuration parameters:
    - format: string to display when DPMS is enabled
    - format_on: (deprecated) old version of format, format will alwayse used if set 
    - format_off: string to display when DPMS is disabled
    - color: color of string if DPMS is enabled
    - color_off: color of string if DPMS is disabled

@author Andre Doser <dosera AT tf.uni-freiburg.de>
"""

from os import system


class Py3status:
    """
    """
    # available configuration parameters
    format_on = None
    format = 'DPMS'
    format_off = 'DPMS'
    color = None
    color_off = None

    def dpms(self, i3s_output_list, i3s_config):
        """
        Display a colorful state of DPMS.
        """
        self.run = system('xset -q | grep -iq "DPMS is enabled"') == 0
        if self.run:
            if self.format_on and self.format is 'DPMS':
                full_text = self.format_on
            else:
                full_text = self.format
            color = self.color or i3s_config['color_good']
        else:
            full_text = self.format_off
            color = self.color_off or i3s_config['color_bad']

        return {
            'full_text': full_text,
            'color': color
        }

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
