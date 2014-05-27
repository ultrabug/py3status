from subprocess import check_output
from time import time

"""
Module for showing current keyboard layout.

Requires:
    - xkblayout-state
    or
    - setxkbmap

@author shadowprince
@license Eclipse Public License
"""

CACHE_TIMEOUT = 10  # refresh time to update indicator

# colors of layouts, check your command's output to match keys
LANG_COLORS = {
    'fr': '#268BD2',  # solarized blue
    'ru': '#F75252',  # red
    'ua': '#FCE94F',  # yellow
    'us': '#729FCF',  # light blue
}


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
    """
    q = check_output(['setxkbmap', '-query']).decode('utf-8')
    return q.replace(' ', '').split(':')[-1]


class Py3status:
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

    def keyboard_layout(self, i3status_output_json, i3status_config):
        response = {
            'full_text': '',
            'name': 'keyboard-layout',
            'cached_until': time() + CACHE_TIMEOUT
        }

        lang = self.command().strip()
        lang_color = LANG_COLORS.get(lang)

        response['full_text'] = lang or '??'
        if lang_color:
            response['color'] = lang_color

        return (0, response)
