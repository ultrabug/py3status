# -*- coding: utf-8 -*-
"""
Microphone control.

Expands on the standard i3status volume module by adding color
and percentage threshold settings.
Volume up/down and Toggle mute via mouse clicks can be easily added see
example.

Configuration parameters:
    button_down: Button to click to decrease volume. Setting to 0 disables.
        (default 0)
    button_mute: Button to click to toggle mute. Setting to 0 disables.
        (default 0)
    button_up: Button to click to increase volume. Setting to 0 disables.
        (default 0)
    cache_timeout: how often we refresh this module in seconds.
        (default 10)
    channel: channel to track. Default value is backend dependent.
        (default None)
    command: Choose between "pamixer" or "pactl".
        If None, try to guess based on available commands.
        (default None)
    device: Device to use. Defaults value is backend dependent
        (default None)
    format: Format of the output.
        (default '😮: {percentage}%')
    format_muted: Format of the output when the volume is muted.
        (default '😶: muted')
    max_volume: Allow the volume to be increased past 100% if available.
        pactl supports this (default 120)
    thresholds: Threshold for percent volume.
        (default [(0, 'bad'), (20, 'degraded'), (50, 'good')])
    volume_delta: Percentage amount that the volume is increased or
        decreased by when volume buttons pressed.
        (default 5)

Format placeholders:
    {percentage} Percentage volume

Color options:
    color_muted: Volume is muted, if not supplied color_bad is used
        if set to `None` then the threshold color will be used.

Example:

```
# Add mouse clicks to change volume
# Set thresholds to rainbow colors

volume_status {
    button_up = 4
    button_down = 5
    button_mute = 2

    thresholds = [
        (0, "#FF0000"),
        (10, "#E2571E"),
        (20, "#FF7F00"),
        (30, "#FFFF00"),
        (40, "#00FF00"),
        (50, "#96BF33"),
        (60, "#0000FF"),
        (70, "#4B0082"),
        (80, "#8B00FF"),
        (90, "#FFFFFF")
    ]
}
```

Requires:
    pamixer or pactl: pulseaudio backend

NOTE:
    If you are changing volume state by external scripts etc and
    want to refresh the module quicker than the i3status interval,
    send a USR1 signal to py3status in the keybinding.
    Example: killall -s USR1 py3status

@author <Jan T> <jans.tuomi@gmail.com>
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u1f62e: 95%'}

mute
{'color': '#FF0000', 'full_text': u'\u1f636: muted'}
"""


from py3status.modules.volume_status import Py3VolStatusBase, AmixerBackend, PamixerBackend, PactlBackend


class Py3status(Py3VolStatusBase):

    def __init__(self):
        self.format = u'😮: {percentage}%'
        self.format_muted = u'😶: muted'

    def post_config_hook(self):
        # Guess command if not set
        if self.command is None:
            self.command = self.py3.check_commands(
                ['pamixer', 'pactl']
            )

        if self.command == 'pamixer':
            self.backend = PamixerBackend(self, False)
        elif self.command == 'pactl':
            self.backend = PactlBackend(self, False)
        else:
            raise NameError("Unknown command")


# test if run directly
if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
