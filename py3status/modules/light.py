# -*- coding: utf-8 -*-
"""
Adjust backlight controllers.

Light is a program to control backlight controllers under GNU/Linux, it is the
successor of lightscript, which was a bash script with the same purpose, and
tries to maintain the same functionality. http://haikarainen.github.io/light

Configuration parameters:
    button_down: mouse button to decrease brightness (default 5)
    button_up: mouse button to increase brightness (default 4)
    cache_timeout: refresh interval for this module (default 60)
    controller: controller to use, otherwise automatic (default None)
    format: display format for this module (default '\u263c {percent:.0f}%')

Format placeholder:
    {percent} percent value, eg 71.43
    {raw} raw value, eg 5
    {raw_maximum} raw maximum value, eg 7

Requires:
    light: command line interface to control backlight controllers

Example:
```
# show raw values
light {
    format = '\u263c {raw}/{raw_maximum}'
}
```

@author lasers

SAMPLE OUTPUT
{'full_text': u'\u263c 71%'}

raw_values
{'full_text': u'\u263c 5/7'}
"""

STRING_NOT_INSTALLED = 'not installed'
STRING_ERROR = 'not supported'


class Py3status:
    """
    """
    # available configuration parameters
    button_down = 5
    button_up = 4
    cache_timeout = 60
    controller = None
    format = u'\u263c {percent:.0f}%'

    def post_config_hook(self):
        self.cmd = 'light %s'
        if not self.py3.check_commands(self.cmd.split()[0]):
            raise Exception(STRING_NOT_INSTALLED)
        if self.controller:
            self.cmd = 'light -s {} %s'.format(self.controller)
        try:
            self.py3.command_output(self.cmd % '-I')
        except:
            raise Exception(STRING_ERROR)
        self.percent = self.py3.format_contains(self.format, 'percent*')
        self.raw = self.py3.format_contains(self.format, 'raw')
        self.raw_maximum = self.py3.command_output(
            self.cmd % '-rm').strip() if self.py3.format_contains(
                self.format, 'raw_maximum') else None

    def lighthouse(self):
        self.py3.command_run(self.cmd % '-O')
        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {
                    'percent': self.py3.command_output(
                        self.cmd % '-p').strip() if self.percent else None,
                    'raw': self.py3.command_output(
                        self.cmd % '-r').strip() if self.raw else None,
                    'raw_maximum': self.raw_maximum
                })}

    def on_click(self, event):
        button = event['button']
        if button == self.button_up:
            self.py3.command_run(self.cmd % '-Ar 1')
        elif button == self.button_down:
            self.py3.command_run(self.cmd % '-Ur 1')


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
