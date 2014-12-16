# -*- coding: utf-8 -*-
"""
Module showing amount of windows at the scratchpad.

@author shadowprince
@license Eclipse Public License
"""

import i3
from time import time


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

    # available configuration parameters
    cache_timeout = 5
    format = "{} ⌫"  # format of indicator. {} replaces with count of windows
    hide_when_none = False  # hide indicator when there is no windows

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
            'cached_until': time() + self.cache_timeout,
            'transformed': transformed
        }
        if self.hide_when_none and count == 0:
            response['full_text'] = ''
        else:
            response['full_text'] = self.format.format(count)

        return response
