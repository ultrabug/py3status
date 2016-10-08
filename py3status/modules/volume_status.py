# -*- coding: utf-8 -*-
"""
Display current sound volume using amixer.

Expands on the standard i3status volume module by adding color
and percentage threshold settings.
Volume up/down and Toggle mute via mouse clicks can be easily added see
example.

Configuration parameters:
    backend: Choose between "alsa" and "pulseaudio"
        (default "alsa")
    button_down: Button to click to decrease volume. Setting to 0 disables.
        (default 0)
    button_mute: Button to click to toggle mute. Setting to 0 disables.
        (default 0)
    button_up: Button to click to increase volume. Setting to 0 disables.
        (default 0)
    cache_timeout: how often we refresh this module in seconds.
        (default 10)
    channel: Alsamixer channel to track (ignored by pulseaudio)
        (default 'Master')
    device: Device to use.
        (default 'default')
    format: Format of the output.
        (default '♪: {percentage}%')
    format_muted: Format of the output when the volume is muted.
        (default '♪: muted')
    threshold_bad: Volume below which color is set to bad.
        (default 20)
    threshold_degraded: Volume below which color is set to degraded.
        (default 50)
    volume_delta: Percentage amount that the volume is increased or
        decreased by when volume buttons pressed.
        (default 5)

Format placeholders:
    {percentage} Percentage volume

Color options:
    color_bad: Volume below threshold_bad or muted
    color_degraded: Volume below threshold_degraded
    color_good: Volume above or equal to threshold_degraded

Example:

```
# Add mouse clicks to change volume

volume_status {
    button_up = 4
    button_down = 5
    button_mute = 2
}
```

Requires:
    alsa-utils: alsa backend (tested with alsa-utils 1.0.29-1)
    pamixer: pulseaudio backend

NOTE:
        If you are changing volume state by external scripts etc and
        want to refresh the module quicker than the i3status interval,
        send a USR1 signal to py3status in the keybinding.
        Example: killall -s USR1 py3status

@author <Jan T> <jans.tuomi@gmail.com>
@license BSD
"""

import re
from os import devnull

from subprocess import check_output, call


class AudioBackend():
    def __init__(self, device, channel):
        self.device = device
        self.channel = channel

    def get_volume(self):
        raise NotImplemented

    def volume_up(self, delta):
        raise NotImplemented

    def volume_down(self, delta):
        raise NotImplemented

    def toggle_mute(self):
        raise NotImplemented


class AlsaBackend(AudioBackend):
    def __init__(self, device, channel):
        AudioBackend.__init__(self, device, channel)
        self.cmd = ['amixer', '-q', '-D', self.device, 'sset', self.channel]

    # return the current channel volume value as a string
    def _get_percentage(self, output):

        # attempt to find a percentage value in square brackets
        p = re.compile(r'(?<=\[)\d{1,3}(?=%\])')
        text = p.search(output).group()

        # check if the parsed value is sane by checking if it's an integer
        try:
            int(text)
            return text

        # if not, show an error message in output
        except ValueError:
            return "error: can't parse amixer output."

    # returns True if the channel is muted
    def _get_muted(self, output):
        p = re.compile(r'(?<=\[)\w{2,3}(?=\])')
        text = p.search(output).group()

        # check if the parsed string is either "off" or "on"
        if text in ['on', 'off']:
            return text == 'off'

        # if not, return False
        else:
            return False

    # this method is called by py3status
    # returns a response dict
    def get_volume(self):

        # call amixer
        output = check_output(['amixer', '-D', self.device, 'sget', self.channel]).decode('utf-8')

        # get the current percentage value
        perc = self._get_percentage(output)

        # get info about channel mute status
        muted = self._get_muted(output)

        return perc, muted

    def volume_up(self, delta):
        # volume up
        DEVNULL = open(devnull, 'wb')
        call(self.cmd + ['{}%+'.format(delta)], stdout=DEVNULL, stderr=DEVNULL)

    def volume_down(self, delta):
        # volume down
        DEVNULL = open(devnull, 'wb')
        call(self.cmd + ['{}%-'.format(delta)], stdout=DEVNULL, stderr=DEVNULL)

    def toggle_mute(self):
        # toggle mute
        DEVNULL = open(devnull, 'wb')
        call(self.cmd + ['toggle'], stdout=DEVNULL, stderr=DEVNULL)


class PulseaudioBackend(AudioBackend):
    def __init__(self, device, channel):
        AudioBackend.__init__(self, device, channel)
        if self.device == 'default':
            self.device = "0"
        self.cmd = ["pamixer", "--sink", self.device]

    def get_volume(self):
        DEVNULL = open(devnull, 'wb')
        perc = check_output(self.cmd + ["--get-volume"]).decode('utf-8').strip()
        muted = (call(self.cmd + ["--get-mute"], stdout=DEVNULL, stderr=DEVNULL) == 0)
        return perc, muted

    def volume_up(self, delta):
        # volume up
        DEVNULL = open(devnull, 'wb')
        call(self.cmd + ["-i", str(delta)], stdout=DEVNULL, stderr=DEVNULL)

    def volume_down(self, delta):
        # volume down
        DEVNULL = open(devnull, 'wb')
        call(self.cmd + ["-d", str(delta)], stdout=DEVNULL, stderr=DEVNULL)

    def toggle_mute(self):
        # toggle mute
        DEVNULL = open(devnull, 'wb')
        call(self.cmd + ["-t"], stdout=DEVNULL, stderr=DEVNULL)


class Py3status:
    """
    """
    # available configuration parameters
    backend = 'alsa'
    button_down = 0
    button_mute = 0
    button_up = 0
    cache_timeout = 10
    channel = 'Master'
    device = 'default'
    format = u'♪: {percentage}%'
    format_muted = u'♪: muted'
    threshold_bad = 20
    threshold_degraded = 50
    volume_delta = 5

    def post_config_hook(self):
        if self.backend == 'alsa':
            self.backend = AlsaBackend(self.device, self.channel)
        elif self.backend == 'pulseaudio':
            self.backend = PulseaudioBackend(self.device, self.channel)
        else:
            raise NameError("Unknown backend")

    # compares current volume to the thresholds, returns a color code
    def _perc_to_color(self, string):
        try:
            value = int(string)
        except ValueError:
            return self.py3.COLOR_BAD

        if value < self.threshold_bad:
            return self.py3.COLOR_BAD
        elif value < self.threshold_degraded:
            return self.py3.COLOR_DEGRADED
        else:
            return self.py3.COLOR_GOOD

    # return the format string formatted with available variables
    def _format_output(self, format, percentage):
        text = self.py3.safe_format(format, {'percentage': percentage})
        return text

    def current_volume(self):
        # call backend
        perc, muted = self.backend.get_volume()

        # determine the color based on the current volume level
        color = self._perc_to_color(perc if not muted else '0')

        # format the output
        text = self._format_output(self.format_muted
                                   if muted else self.format, perc)
        # create response dict
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
            'full_text': text,
        }
        return response

    def on_click(self, event):
        '''
        Volume up/down and toggle mute.
        '''
        button = event['button']
        # volume up
        if self.button_up and button == self.button_up:
            self.backend.volume_up(self.volume_delta)
        # volume down
        elif self.button_down and button == self.button_down:
            self.backend.volume_down(self.volume_delta)
        # toggle mute
        elif self.button_mute and button == self.button_mute:
            self.backend.toggle_mute()


# test if run directly
if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
