# -*- coding: utf-8 -*-

"""
Switch between horizontal and vertical screen rotation on a single click.

Configuration parameters:
    - cache_timeout: how often to refresh this module.
        default is 10
    - format: a string that formats the output, can include placeholders.
        default is '{icon}'
    - horizontal_icon: a character to represent horizontal rotation.
        default is 'H'
    - horizontal_rotation: a horizontal rotation for xrandr to use.
        available options: 'normal' or 'inverted'.
        default is 'normal'
    - vertical_icon: a character to represent vertical rotation.
        default is 'V'
    - vertical_rotation: a vertical rotation for xrandr to use.
        available options: 'left' or 'right'.
        default is 'left'

Available placeholders for formatting the output:
    - {icon} a rotation icon, specified by `horizontal_icon` or `vertical_icon`.


@author Maxim Baz (https://github.com/maximbaz)
@license BSD
"""

from subprocess import Popen, PIPE
from time import sleep, time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{icon}'
    horizontal_icon = 'H'
    horizontal_rotation = 'normal'
    vertical_icon = 'V'
    vertical_rotation = 'left'

    def _call(self, cmd):
        output = Popen(cmd, stdout=PIPE, shell=True).stdout.readline()
        try:
            # python3
            output = output.decode()
        except:
            pass
        return output.strip()

    def _get_first_output(self):
        cmd = 'xrandr -q --verbose | grep " connected [^(]" | cut -d " " -f1'
        return self._call(cmd)

    def _get_current_rotation_icon(self):
        output = self._get_first_output()
        cmd = 'xrandr -q --verbose | grep "^' + output + '" | cut -d " " -f5'
        is_horizontal = self._call(cmd) in ['normal', 'inverted']
        return self.horizontal_icon if is_horizontal else self.vertical_icon

    def _apply(self):
        rotation = self.horizontal_rotation if self.displayed == self.horizontal_icon else self.vertical_rotation
        output = self._get_first_output()
        cmd = 'xrandr --output ' + output + ' --rotate ' + rotation
        self._call(cmd)

    def _switch_selection(self):
        self.displayed = self.vertical_icon if self.displayed == self.horizontal_icon else self.horizontal_icon

    def on_click(self, i3s_output_list, i3s_config, event):
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

    def xrandr_rotate(self, i3s_output_list, i3s_config):
        if not hasattr(self, 'displayed'):
            self.displayed = self._get_current_rotation_icon()

        full_text = self.format.format(icon=self.displayed or '?')

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': full_text
        }

        # coloration
        if self.displayed == self._get_current_rotation_icon():
            response['color'] = i3s_config['color_good']

        return response


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.xrandr_rotate([], config))
        sleep(1)
