# -*- coding: utf-8 -*-
"""
Adjust screen backlight brightness.

Configuration parameters:
    brightness_delta: Change the brightness by this step.
        (default 5)
    brightness_initial: Set brightness to this value on start.
        (default None)
    brightness_minimal: Don't go below this brightness to avoid black screen
        (default 1)
    button_down: Button to click to decrease brightness. Setting to 0 disables.
        (default 5)
    button_up: Button to click to increase brightness. Setting to 0 disables.
        (default 4)
    cache_timeout: How often we refresh this module in seconds (default 10)
    device: The backlight device
        If not specified the plugin will detect it automatically
        (default None)
    device_path: path to backlight eg /sys/class/backlight/acpi_video0
        if None then use first device found.
        (default None)
    format: Display brightness, see placeholders below
        (default '☼: {level}%')

Format status string parameters:
    {level} brightness

Requires:
    xbacklight: need for changing brightness, not detection

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD

SAMPLE OUTPUT
{'full_text': u'\u263c: 100%'}
"""

from __future__ import division

import os


def get_device_path():
    for (path, devices, files) in os.walk('/sys/class/backlight/'):
        for device in devices:
            if 'brightness' in os.listdir(path + device) and \
               'max_brightness' in os.listdir(path + device):
                return path + device


class Py3status:
    """
    """
    # available configuration parameters
    brightness_delta = 5
    brightness_initial = None
    brightness_minimal = 1
    button_down = 5
    button_up = 4
    cache_timeout = 10
    device = None
    device_path = None
    format = u'☼: {level}%'

    def post_config_hook(self):
        if not self.device:
            self.device_path = get_device_path()
        else:
            self.device_path = "/sys/class/backlight/%s" % self.device
        self.xbacklight = self.py3.check_commands(['xbacklight'])
        if self.xbacklight and self.brightness_initial:
            self._set_backlight_level(self.brightness_initial)

    def on_click(self, event):
        if not self.xbacklight:
            return None

        level = self._get_backlight_level()
        button = event['button']
        if self.button_up and button == self.button_up:
            level += self.brightness_delta
            if level > 100:
                level = 100
        elif self.button_down and button == self.button_down:
            level -= self.brightness_delta
            if level < self.brightness_minimal:
                level = self.brightness_minimal
        self._set_backlight_level(level)

    def _set_backlight_level(self, level):
        self.py3.command_run(['xbacklight', '-set', str(level)])

    def _get_backlight_level(self):
        for brightness_line in open("%s/brightness" % self.device_path, 'rb'):
            brightness = int(brightness_line)
        for brightness_max_line in open("%s/max_brightness" % self.device_path, 'rb'):
            brightness_max = int(brightness_max_line)
        return brightness * 100 // brightness_max

    def backlight(self):
        full_text = ""
        if self.device_path is not None:
            level = self._get_backlight_level()
            full_text = self.py3.safe_format(self.format, {'level': level})

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
