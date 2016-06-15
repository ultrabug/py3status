# -*- coding: utf-8 -*-
"""
Display the current active keyboard layout.

Configuration parameters:
    cache_timeout: check for keyboard layout change every seconds
    color: a single color value for all layouts. eg: "#FCE94F"
    colors: a comma separated string of color values for each layout,
        eg: "us=#FCE94F, fr=#729FCF".
    format: see placeholders below

Format of status string placeholders:
    {layout} currently active keyboard layout

Requires:
    xkblayout-state:
        or
    setxkbmap: and `xset` (works for the first two predefined layouts.)

@author shadowprince, tuxitop
@license Eclipse Public License
"""

from subprocess import check_output
from time import time
import re


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    color = None
    colors = 'us=#729FCF, fr=#268BD2, ua=#FCE94F, ru=#F75252'
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

    def keyboard_layout(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }
        if not self.color:
            self.colors_dict = dict((k.strip(), v.strip()) for k, v in (
                layout.split('=') for layout in self.colors.split(',')))
        lang = self._command().strip() or '??'
        lang_color = self.color if self.color else self.colors_dict.get(lang)
        if lang_color:
            response['color'] = lang_color

        response['full_text'] = self.format.format(layout=lang)
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
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_degraded': '#FFFF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.keyboard_layout([], config))
        sleep(1)
