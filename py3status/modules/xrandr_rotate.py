# -*- coding: utf-8 -*-

"""
Control screen rotation.

Configuration parameters:
    cache_timeout: how often to refresh this module.
        (default 10)
    format: a string that formats the output, can include placeholders.
        (default '{icon}')
    hide_if_disconnected: a boolean flag to hide icon when `screen` is
        disconnected.
        It has no effect unless `screen` option is also configured.
        (default False)
    horizontal_icon: a character to represent horizontal rotation.
        (default 'H')
    horizontal_rotation: a horizontal rotation for xrandr to use.
        Available options: 'normal' or 'inverted'.
        (default 'normal')
    screen: display output name to rotate, as detected by xrandr.
        If not provided, all enabled screens will be rotated.
        (default None)
    vertical_icon: a character to represent vertical rotation.
        (default 'V')
    vertical_rotation: a vertical rotation for xrandr to use.
        Available options: 'left' or 'right'.
        (default 'left')

Format placeholders:
    {icon} a rotation icon, specified by `horizontal_icon` or `vertical_icon`.
    {screen} a screen name, specified by `screen` option or detected
        automatically if only one screen is connected, otherwise 'ALL'.

Color options:
    color_degraded: Screen is disconnected
    color_good: Displayed rotation is active

@author Maxim Baz (https://github.com/maximbaz)
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'V'}

h
{'color': '#00FF00', 'full_text': u'H'}
"""

from subprocess import Popen, PIPE


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{icon}'
    hide_if_disconnected = False
    horizontal_icon = 'H'
    horizontal_rotation = 'normal'
    screen = None
    vertical_icon = 'V'
    vertical_rotation = 'left'

    def __init__(self):
        self.displayed = ''

    def _call(self, cmd):
        process = Popen(cmd, stdout=PIPE, shell=True)
        output = process.communicate()[0] or ""
        try:
            # python3
            output = output.decode()
        except:
            pass
        return output.strip()

    def _get_all_outputs(self):
        cmd = 'xrandr -q | grep " connected [^(]" | cut -d " " -f1'
        return self._call(cmd).split()

    def _get_current_rotation_icon(self, all_outputs):
        output = self.screen or all_outputs[0]
        cmd = 'xrandr -q | grep "^' + output + '" | cut -d " " -f4'
        output = self._call(cmd)
        # xrandr may skip printing the 'normal', in which case the output would
        # start from '('
        is_horizontal = (output.startswith('(') or
                         output in ['normal', 'inverted'])
        return self.horizontal_icon if is_horizontal else self.vertical_icon

    def _apply(self):
        if self.displayed == self.horizontal_icon:
            rotation = self.horizontal_rotation
        else:
            rotation = self.vertical_rotation
        outputs = [self.screen] if self.screen else self._get_all_outputs()
        for output in outputs:
            cmd = 'exec xrandr --output ' + output + ' --rotate ' + rotation
            Popen(['i3-msg', cmd], stdout=PIPE)

    def _switch_selection(self):
        if self.displayed == self.horizontal_icon:
            self.displayed = self.vertical_icon
        else:
            self.displayed = self.horizontal_icon

    def on_click(self, event):
        """
        Click events
            - left click & scroll up/down: switch between rotations
            - right click: apply selected rotation
        """
        button = event['button']
        if button in [1, 4, 5]:
            self._switch_selection()
        elif button == 3:
            self._apply()

    def xrandr_rotate(self):
        all_outputs = self._get_all_outputs()
        selected_screen_disconnected = (
            self.screen is not None and self.screen not in all_outputs
        )
        if selected_screen_disconnected and self.hide_if_disconnected:
            self.displayed = ''
            full_text = ''
        else:
            if not self.displayed:
                self.displayed = self._get_current_rotation_icon(all_outputs)

            if len(all_outputs) == 1:
                screen = self.screen or all_outputs[0]
            else:
                screen = 'ALL'
            full_text = self.py3.safe_format(self.format,
                                             dict(icon=self.displayed or '?',
                                                  screen=screen))

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text
        }

        # coloration
        if selected_screen_disconnected and not self.hide_if_disconnected:
            response['color'] = self.py3.COLOR_DEGRADED
        elif self.displayed == self._get_current_rotation_icon(all_outputs):
            response['color'] = self.py3.COLOR_GOOD

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
