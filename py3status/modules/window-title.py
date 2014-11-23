import i3
from time import time

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

CACHE_TIMEOUT = 0.5  # maximum time to update indicator
MAX_WIDTH = 120  # if width of title is greater, shrink it and add '...'
POSITION = 0


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
    def __init__(self):
        self.text = ''

    def window_title(self, i3_status_output_json, i3status_config):
        window = find_focused(i3.get_tree())

        transformed = False
        if window and 'name' in window and window['name'] != self.text:
            self.text = len(window['name']) > MAX_WIDTH and "..." + window['name'][-(MAX_WIDTH-3):] or window['name']
            transformed = True

        response = {
            'cached_until': time() + CACHE_TIMEOUT,
            'full_text': self.text,
            'name': 'window-title',
            'transformed': transformed
        }

        return (POSITION, response)
