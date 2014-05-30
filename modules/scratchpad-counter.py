# -*- coding: utf-8 -*-

import i3
from time import time

"""
Module showing amount of windows at the scratchpad.

@author shadowprince
@license Eclipse Public License
"""

CACHE_TIMEOUT = 5
HIDE_WHEN_NONE = False  # hide indicator when there is no windows
POSITION = 0
STRFORMAT = "{} ⌫"  # format of indicator. {} replaces with count of windows


def find_scratch(tree):
    if tree["name"] == "__i3_scratch":
        return tree
    else:
        for x in tree["nodes"]:
            result = find_scratch(x)
            if result:
                return result
        return None


class Py3status:
    def __init__(self):
        self.count = -1

    def scratchpad_counter(self, i3status_output_json, i3status_config):
        count = len(find_scratch(i3.get_tree()).get("floating_nodes", []))

        if self.count != count:
            transformed = True
            self.count = count
        else:
            transformed = False

        response = {
            'cached_until': time() + CACHE_TIMEOUT,
            'full_text': '' if HIDE_WHEN_NONE and count == 0 else STRFORMAT.format(count),
            'name': 'scratchpad-counter',
            'transformed': transformed
        }

        return (POSITION, response)
