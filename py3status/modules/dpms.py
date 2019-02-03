# -*- coding: utf-8 -*-
"""
Turn on and off DPMS and screen saver blanking.

Configuration parameters:
    button_off: mouse button to turn off screen (default None)
    button_toggle: mouse button to toggle DPMS (default 1)
    cache_timeout: refresh interval for this module (default 15)
    format: display format for this module (default '{icon}')
    icon_off: show when DPMS is disabled (default 'DPMS')
    icon_on: show when DPMS is enabled (default 'DPMS')

Format placeholders:
    {icon} DPMS icon

Color options:
    color_on: Enabled, defaults to color_good
    color_off: Disabled, defaults to color_bad

@author Andre Doser <dosera AT tf.uni-freiburg.de>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'DPMS'}

off
{'color': '#FF0000', 'full_text': 'DPMS'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    button_off = None
    button_toggle = 1
    cache_timeout = 15
    format = "{icon}"
    icon_off = "DPMS"
    icon_on = "DPMS"

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "format_on",
                    "new": "icon_on",
                    "msg": "obsolete parameter use `icon_on`",
                },
                {
                    "param": "format_off",
                    "new": "icon_off",
                    "msg": "obsolete parameter use `icon_off`",
                },
            ]
        }

    def post_config_hook(self):
        self.color_on = self.py3.COLOR_ON or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_OFF or self.py3.COLOR_BAD

    def dpms(self):
        """
        Display a colorful state of DPMS.
        """
        if "DPMS is Enabled" in self.py3.command_output("xset -q"):
            _format = self.icon_on
            color = self.color_on
        else:
            _format = self.icon_off
            color = self.color_off

        icon = self.py3.safe_format(_format)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"icon": icon}),
            "color": color,
        }

    def on_click(self, event):
        """
        Control DPMS with mouse clicks.
        """
        if event["button"] == self.button_toggle:
            if "DPMS is Enabled" in self.py3.command_output("xset -q"):
                self.py3.command_run("xset -dpms s off")
            else:
                self.py3.command_run("xset +dpms s on")

        if event["button"] == self.button_off:
            self.py3.command_run("xset dpms force off")


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
