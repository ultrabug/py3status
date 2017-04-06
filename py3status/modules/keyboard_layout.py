# -*- coding: utf-8 -*-
"""
Display keyboard layout.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    colors: deprecated. see color options below (default None)
    format: display format for this module (default '{layout}')

Format placeholders:
    {layout} keyboard layout

Color options:
    color_<layout>: colorize the layout. eg color_fr = '#729FCF'

Requires:
    xkblayout-state:
        or
    setxkbmap: and `xset` (works for the first two predefined layouts.)

@author shadowprince, tuxitop
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': 'gb'}

fr
{'color': '#268BD2', 'full_text': 'fr'}

ru
{'color': '#F75252', 'full_text': 'ru'}

ua
{'color': '#FCE94F', 'full_text': 'ua'}

us
{'color': '#729FCF', 'full_text': 'us'}

"""

import re
LAYOUTS_RE = re.compile(r".*layout:\s*((\w+,?)+).*", flags=re.DOTALL)
LEDMASK_RE = re.compile(r".*LED\smask:\s*\d{4}([01])\d{3}.*", flags=re.DOTALL)


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    colors = None
    format = '{layout}'

    def post_config_hook(self):
        try:
            self._xkblayout()
            self._command = self._xkblayout
        except:
            self._command = self._setxkbmap

        self.colors_dict = {}
        # old compatability: set default values
        self.defaults = {
            'fr': '#268BD2',
            'ru': '#F75252',
            'ua': '#FCE94F',
            'us': '#729FCF',
        }

    def keyboard_layout(self):
        lang = self._command().strip() or '??'
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'layout': lang})
        }

        if self.colors and not self.colors_dict:
            self.colors_dict = dict((k.strip(), v.strip()) for k, v in (
                layout.split('=') for layout in self.colors.split(',')))

        lang_color = getattr(self.py3, 'COLOR_%s' % lang.upper())
        if not lang_color:
            lang_color = self.colors_dict.get(lang)
        if not lang_color:  # old compatability: try default value
            lang_color = self.defaults.get(lang)
        if lang_color:
            response['color'] = lang_color

        return response

    def _xkblayout(self):
        return self.py3.command_output(["xkblayout-state", "print", "%s"])

    def _setxkbmap(self):
        # this method works only for the first two predefined layouts.
        out = self.py3.command_output(["setxkbmap", "-query"])
        layouts = re.match(LAYOUTS_RE, out).group(1).split(",")
        if len(layouts) == 1:
            return layouts[0]

        xset_output = self.py3.command_output(["xset", "-q"])
        led_mask = re.match(LEDMASK_RE, xset_output).groups(0)[0]
        return layouts[int(led_mask)]


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
