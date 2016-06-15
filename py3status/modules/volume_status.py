# -*- coding: utf-8 -*-
"""
Display current sound volume using amixer.

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
    channel: Alsamixer channel to track.
        (default 'Master')
    device: Alsamixer device to use.
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

Format status string parameters:
    {percentage} Percentage volume

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
    alsa-utils: (tested with alsa-utils 1.0.29-1)

NOTE:
        If you are changing volume state by external scripts etc and
        want to refresh the module quicker than the i3status interval,
        send a USR1 signal to py3status in the keybinding.
        Example: killall -s USR1 py3status

@author <Jan T> <jans.tuomi@gmail.com>
@license BSD
"""

import re
import shlex

from subprocess import check_output, call
from time import time


class Py3status:
    """
    """
    # available configuration parameters
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

    # compares current volume to the thresholds, returns a color code
    def _perc_to_color(self, i3s_config, string):
        try:
            value = int(string)
        except ValueError:
            return i3s_config['color_bad']

        if value < self.threshold_bad:
            return i3s_config['color_bad']
        elif value < self.threshold_degraded:
            return i3s_config['color_degraded']
        else:
            return i3s_config['color_good']

    # return the format string formatted with available variables
    def _format_output(self, format, percentage):
        text = format.format(percentage=percentage)
        return text

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

    # this method is ran by py3status
    # returns a response dict
    def current_volume(self, i3s_output_list, i3s_config):

        # call amixer
        output = check_output(shlex.split('amixer -D {} sget {}'.format(
            self.device, self.channel))).decode('utf-8')

        # get the current percentage value
        perc = self._get_percentage(output)

        # get info about channel mute status
        muted = self._get_muted(output)

        # determine the color based on the current volume level
        color = self._perc_to_color(i3s_config, perc)

        # format the output
        text = self._format_output(self.format_muted
                                   if muted else self.format, perc)
        # create response dict
        response = {
            'cached_until': time() + self.cache_timeout,
            'color': color,
            'full_text': text,
        }
        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        '''
        Volume up/down and toggle mute.
        '''
        button = event['button']
        cmd = 'amixer -q -D {} sset {} '.format(self.device, self.channel)
        # volume up
        if self.button_up and button == self.button_up:
            call(shlex.split('{} {}%+'.format(cmd, self.volume_delta)))
        # volume down
        elif self.button_down and button == self.button_down:
            call(shlex.split('{} {}%-'.format(cmd, self.volume_delta)))
        # toggle mute
        elif self.button_mute and button == self.button_mute:
            call(shlex.split('{} toggle'.format(cmd)))


# test if run directly
if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }

    while True:
        print(x.current_volume([], config))
        sleep(1)
