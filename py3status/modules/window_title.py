# -*- coding: utf-8 -*-
"""
Py3status plugin - shows current window title.

Requires:
    - i3-py (https://github.com/ziberna/i3-py)
    # pip install i3-py

If payload from server contains wierd utf-8
(for example one window have something bad in title) - the plugin will
give empty output UNTIL this window is closed.
I can't fix or workaround that in PLUGIN, problem is in i3-py library.

@author shadowprince
@license Eclipse Public License
"""

import i3
from time import time


def find_focused(tree):
    if type(tree) == list:
        for el in tree:
            res = find_focused(el)
            if res:
                return res
    elif type(tree) == dict:
        if tree['focused']:
            return tree
        else:
            return find_focused(tree['nodes'] + tree['floating_nodes'])


class Py3status:

    # available configuration parameters
    cache_timeout = 0.5
    max_width = 120  # if width of title is greater, shrink it and add '...'

    def __init__(self):
        self.text = ''

    def window_title(self, i3s_output_list, i3s_config):
        window = find_focused(i3.get_tree())

        transformed = False
        if window and 'name' in window and window['name'] != self.text:
            self.text = (
                len(window['name']) > self.max_width
                and "..." + window['name'][-(self.max_width-3):]
                or window['name']
            )
            transformed = True

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': self.text,
            'transformed': transformed
        }
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.window_title([], {}))
        sleep(1)
