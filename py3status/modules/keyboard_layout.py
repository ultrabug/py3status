# -*- coding: utf-8 -*-
"""
Display the current keyboard layout.

Requires:
    - xkblayout-state
    or
    - setxkbmap

@author shadowprince
@license Eclipse Public License
"""

from subprocess import check_output
from time import time
import shlex
import re

# colors of layouts, check your command's output to match keys
LANG_COLORS = {
    'fr': '#268BD2',  # solarized blue
    'ru': '#F75252',  # red
    'ua': '#FCE94F',  # yellow
    'us': '#729FCF',  # light blue
}

LAYOUT_RE = re.compile(r".*layout:\s*(\w+).*", flags=re.DOTALL)


def xbklayout():
    """
    check using xkblayout-state (preferred method)
    """
    return check_output(
        ["xkblayout-state", "print", "%s"]
    ).decode('utf-8')


def setxkbmap():
    """
    check using setxkbmap >= 1.3.0

    Please read issue 33 for more information :
        https://github.com/ultrabug/py3status/pull/33
    """
    out = check_output(shlex.split("setxkbmap -query")).decode("utf-8")

    return re.match(LAYOUT_RE, out).group(1)


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    color = ''

    def __init__(self):
        """
        find the best implementation to get the keyboard's layout
        """
        try:
            xbklayout()
        except:
            self.command = setxkbmap
        else:
            self.command = xbklayout

    def keyboard_layout(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }

        lang = self.command().strip()
        lang_color = self.color if self.color else LANG_COLORS.get(lang)

        response['full_text'] = lang or '??'
        if lang_color:
            response['color'] = lang_color

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.keyboard_layout([], config))
        sleep(1)
