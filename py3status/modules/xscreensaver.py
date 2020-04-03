"""
Control Xscreensaver.

This script is useful for people who let Xscreensaver manage DPMS settings.
Xscreensaver has its own DPMS variables separate from xset. DPMS can be
safely turned off in xset as long as Xscreensaver is running.
Settings can be managed using "xscreensaver-demo".

Configuration parameters:
    button_activate: mouse button to activate Xscreensaver (default 3)
    button_toggle: mouse button to toggle Xscreensaver (default 1)
    cache_timeout: refresh interval for this module (default 15)
    format: display format for this module (default '{icon}')
    icon_off: show when Xscreensaver is not running (default 'XSCR')
    icon_on: show when Xscreensaver is running (default 'XSCR')

Format placeholders:
    {icon} Xscreensaver icon

Color options:
    color_on: Enabled, defaults to color_good
    color_off: Disabled, defaults to color_bad

@author neutronst4r, lasers

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'XSCR'}

off
{'color': '#FF0000', 'full_text': 'XSCR'}
"""

from os import setpgrp
from subprocess import Popen, PIPE

STRING_UNAVAILABLE = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    button_activate = 3
    button_toggle = 1
    cache_timeout = 15
    format = "{icon}"
    icon_off = "XSCR"
    icon_on = "XSCR"

    def post_config_hook(self):
        self.color_on = self.py3.COLOR_ON or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_OFF or self.py3.COLOR_BAD
        if not self.py3.check_commands(["xscreensaver"]):
            raise Exception(STRING_UNAVAILABLE)

    def _is_running(self):
        try:
            self.py3.command_output(["pidof", "xscreensaver"])
            return True
        except self.py3.CommandError:
            return False

    def xscreensaver(self):
        run = self._is_running()
        if run:
            icon = self.icon_on
            color = self.color_on
        else:
            icon = self.icon_off
            color = self.color_off

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"icon": icon}),
            "color": color,
        }

    def on_click(self, event):
        run = self._is_running()
        if event["button"] == self.button_activate:
            self.py3.command_run(["xscreensaver-command", "-activate"])

        if event["button"] == self.button_toggle:
            if run:
                self.py3.command_run(["xscreensaver-command", "-exit"])
            else:
                # Because we want xscreensaver to continue running after
                # exit, we instead use preexec_fn=setpgrp here.
                Popen(
                    ["xscreensaver", "-no-splash", "-no-capture-stderr"],
                    stdout=PIPE,
                    stderr=PIPE,
                    preexec_fn=setpgrp,
                )


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
