# -*- coding: utf-8 -*-
"""
This module allows activation and deactivation
of DPMS (Display Power Management Signaling)
by clicking on 'DPMS' in the status bar.

Written and contributed by @tasse:
    Andre Doser <dosera AT tf.uni-freiburg.de>
"""

from os import system


class Py3status:
    def __init__(self):
        """
        Detect current state on start.
        """
        self.run = system('xset -q | grep -iq "DPMS is enabled"') == 0

    def dpms(self, i3s_output_list, i3s_config):
        """
        Display a colorful state of DPMS.
        """
        response = {
            'full_text': 'DPMS'
        }
        if self.run:
            response['color'] = i3s_config['color_good']
        else:
            response['color'] = i3s_config['color_bad']
        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Enable/Disable DPMS on left click.
        """
        if event['button'] == 1:
            if self.run:
                self.run = False
                system("xset -dpms")
            else:
                self.run = True
                system("xset +dpms")
            system("killall -USR1 py3status")
