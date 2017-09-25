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
    delta: specify raw or percent value to use, eg 5, '5 raw', '5r', '5p',
        '5 perc', '5 percent', et cetera. otherwise 1, in raw (default None)
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

# adjust delta by percent
light {
    delta = '5 percent'
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
    delta = None
    format = '\u263c {percent:.0f}%'

    def post_config_hook(self):
        if not self.py3.check_commands('light'):
            raise Exception(STRING_NOT_INSTALLED)
        try:
            self.py3.command_output('light')
        except:
            raise Exception(STRING_ERROR)
        self.cmd = cmd_set = 'light -s {} %s'.format(
            self.controller) if self.controller else 'light %s'

        if self.delta is None:
            cmd_set %= '-r %s'
            self.delta = 1
        elif not isinstance(self.delta, int):
            percent = any([x for x in self.delta if x.lower() == 'p'])
            try:
                self.delta = int(''.join(x for x in self.delta if x.isdigit()))
            except:
                self.delta = 1
            self.delta = 1 if self.delta == 0 else self.delta
            cmd_set %= '-p %s' if percent else '-r %s'
        self.up = cmd_set % '-A %s' % self.delta
        self.down = cmd_set % '-U %s' % self.delta

        self.percent = self.py3.format_contains(self.format, 'percent*')
        self.raw = self.py3.format_contains(self.format, 'raw')
        self.raw_maximum = self.py3.command_output(
            self.cmd % '-rm').strip() if self.py3.format_contains(
                self.format, 'raw_maximum') else None

    def lighthouse(self):
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
            self.py3.command_run(self.up)
        elif button == self.button_down:
            self.py3.command_run(self.down)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
