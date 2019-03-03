# -*- coding: utf-8 -*-
"""
Control redshift in continuous mode.

Allows to toggle redshift running in continuous mode (as opposed to hueshift
module). Can display current parameters like color temperature, period of day
and screen brightness.

Configuration parameters:
    button_toggle: Mouse button to toggle redshift.
        (default 1)
    cache_timeout: How often this module is refreshed.
        (default 10)
    format: Display format to use.
        (default 'Redshift: [\?if=enabled {period} {temperature}K|off]')

Control placeholders:
    {enabled} boolean value set based on pgrep, eg False, True

Format placeholders:
    {brightness} brightness of the screen
    {period} period of the day
    {temperature} color temperature
    {transition} progress of the day-night transition

Requires:
    redshift: program to adjust color temperature of the screen

@author Bazyli Cyran (https://github.com/sajran)

SAMPLE OUTPUT
{'full_text': u'Redshift 3500K ', 'cached_until': 1551641858.0}

off
{'full_text': u'Redshift: off', 'cached_until': 1551643892.0}
"""

import subprocess
import os
import re

STRING_NOT_INSTALLED = "redshift is not installed"


class Py3status:
    """
    """

    # available configuration parameters
    button_toggle = 1
    cache_timeout = 10
    format = "Redshift: [\?if=enabled {period} {temperature}K|off]"

    def post_config_hook(self):
        if not self.py3.check_commands("redshift"):
            raise Exception(STRING_NOT_INSTALLED)

        self.period_re = "Period: (\w*)"
        self.temperature_re = "Color temperature: (\d*)K"
        self.brightness_re = "Brightness: ([\d.]*)"
        self.transition_re = "Transition \(([\d.]*)%"

    def _check_status(self):
        try:
            self.py3.command_output("pgrep -x redshift")
            self.enabled = True
        except self.py3.CommandError:
            self.enabled = False

        details = self.py3.command_output("redshift -p")
        self.period = re.search(self.period_re, details).group(1).lower()
        self.temperature = re.search(self.temperature_re, details).group(1)
        self.brightness = re.search(self.brightness_re, details).group(1)
        self.brightness = int(float(self.brightness) * 100)

        if self.period == "transition":
            self.transition = re.search(self.transition_re, details).group(1)
        else:
            self.transition = False

    def _toggle(self):
        if (self.enabled):
            self.py3.command_run("killall redshift")
        else:
            DEVNULL = open(os.devnull, "w")
            subprocess.Popen("redshift", stdout=DEVNULL, preexec_fn=os.setpgrp)

    def redshift(self):
        self._check_status()

        redshift_data = {
            "enabled": self.enabled,
            "period": self.period,
            "temperature": self.temperature,
            "brightness": self.brightness,
            "transition": self.transition
        }

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, redshift_data)
        }

    def on_click(self, event):
        button = event["button"]

        if button == self.button_toggle:
            self._toggle()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
