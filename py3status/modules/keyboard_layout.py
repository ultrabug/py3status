# -*- coding: utf-8 -*-
"""
Display keyboard layout.

Configuration parameters:
    cache_timeout: check for keyboard layout change every seconds (default 10)
    colors: a comma separated string of color values for each layout,
        eg: "us=#FCE94F, fr=#729FCF". (deprecated use color options)
         (default None)
    format: see placeholders below (default '{layout}')

Format placeholders:
    {layout} currently active keyboard layout

Color options:
    color_<layout>: color for the layout
        eg color_fr = '#729FCF'

Requires:
    xkblayout-state:
        or
    setxkbmap: and `xset` (works for the first two predefined layouts.)

@author shadowprince, tuxitop
@license Eclipse Public License
"""

from subprocess import check_output
import re


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    colors = None
    format = '{layout}'

    def __init__(self):
        """
        find the best implementation to get the keyboard's layout
        """
        try:
            self._xkblayout()
            self._command = self._xkblayout
        except:
            self._command = self._xset
        self.colors_dict = {}
        # old default values for backwards compatability
        self.defaults = {
            'fr': '#268BD2',
            'ru': '#F75252',
            'ua': '#FCE94F',
            'us': '#729FCF',
        }

    def keyboard_layout(self):
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': ''
        }
        if self.colors and not self.colors_dict:
            self.colors_dict = dict((k.strip(), v.strip()) for k, v in (
                layout.split('=') for layout in self.colors.split(',')))

        lang = self._command().strip() or '??'

        lang_color = getattr(self.py3, 'COLOR_%s' % lang.upper())
        if not lang_color:
            lang_color = self.colors_dict.get(lang)
        if not lang_color:
            # If not found try to use old default value
            lang_color = self.defaults.get(lang)

        if lang_color:
            response['color'] = lang_color

        response['full_text'] = self.py3.safe_format(self.format, {'layout': lang})
        return response

    def _get_layouts(self):
        """
        Returns a list of predefined keyboard layouts
        """
        layouts_re = re.compile(r".*layout:\s*((\w+,?)+).*", flags=re.DOTALL)
        out = check_output(["setxkbmap", "-query"]).decode("utf-8")
        layouts = re.match(layouts_re, out).group(1).split(",")
        return layouts

    def _xkblayout(self):
        """
        check using xkblayout-state
        """
        return check_output(["xkblayout-state", "print", "%s"]).decode('utf-8')

    def _xset(self):
        """
        Check using setxkbmap >= 1.3.0 and xset
        This method works only for the first two predefined layouts.
        """
        ledmask_re = re.compile(r".*LED\smask:\s*\d{4}([01])\d{3}.*",
                                flags=re.DOTALL)
        layouts = self._get_layouts()
        if len(layouts) == 1:
            return layouts[0]
        xset_output = check_output(["xset", "-q"]).decode("utf-8")
        led_mask = re.match(ledmask_re, xset_output).groups(0)[0]
        return layouts[int(led_mask)]


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
