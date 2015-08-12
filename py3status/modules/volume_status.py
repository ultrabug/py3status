# -*- coding: utf-8 -*-
"""
Display current sound volume using amixer.

Expands on the standard i3status volume module by adding color
and percentage threshold settings.

Configuration parameters:
    - cache_timeout : how often we refresh this module in seconds (10s default)
    - channel : "Master" by default, alsamixer channel to track
    - device : "default" by default, alsamixer device to use
    - format : format the output, available variables: {percentage}
    - format_muted : format the output when the volume is muted
    - threshold_bad : 20 by default
    - threshold_degraded : 50 by default

Requires:
    alsa-utils (tested with alsa-utils 1.0.29-1)

NOTE:
    If you want to refresh the module quicker than the i3status interval,
    send a USR1 signal to py3status in the keybinding.
    Example: killall -s USR1 py3status

@author <Jan T> <jans.tuomi@gmail.com>
@license BSD
"""

import re
import shlex

from subprocess import check_output
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    channel = 'Master'
    device = 'default'
    format = u'♪: {percentage}%'
    format_muted = u'♪: muted'
    threshold_bad = 20
    threshold_degraded = 50

    # constructor
    def __init__(self):
        self.text = ''

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

        # if the text has been changed, update the cached text and
        # set transformed to True
        transformed = text != self.text
        self.text = text

        # create response dict
        response = {
            'cached_until': time() + self.cache_timeout,
            'color': color,
            'full_text': text,
            'transformed': transformed
        }
        return response

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
