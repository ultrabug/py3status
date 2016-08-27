# -*- coding: utf-8 -*-
"""
Display the amount of windows in your i3 scratchpad.

@author shadowprince
@license Eclipse Public License
"""

import i3


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
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = "{} ⌫"  # format of indicator. {} replaces with count of windows
    hide_when_none = False  # hide indicator when there is no windows

    def __init__(self):
        self.count = -1

    def scratchpad_counter(self):
        count = len(find_scratch(i3.get_tree()).get("floating_nodes", []))

        if self.count != count:
            transformed = True
            self.count = count
        else:
            transformed = False

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'transformed': transformed
        }
        if self.hide_when_none and count == 0:
            response['full_text'] = ''
        else:
            response['full_text'] = self.format.format(count)

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
