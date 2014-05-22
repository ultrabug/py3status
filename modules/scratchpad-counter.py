import i3
import time
import random
from pprint import pprint

"""
Module showing amount of windows at the scratchpad.

@author shadowprince
@version 1.0
@license Eclipse Public License
"""

CACHED_TIME = 1
POSITION = 1
HIDE_WHEN_NONE = True # hide indicator when there is no windows
STRFORMAT = "{} ⌫" # format of indicator. {} replaces with count of windows

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
    def __init__(self, *args, **kwargs):
        self.count = -1
        super(Py3status).__init__(*args, **kwargs)

    def scratchpadCounter(self, i3status_output_json, i3status_config):
        count = len(find_scratch(i3.get_tree()).get("floating_nodes", []))

        if self.count != count:
            transformed = True
            self.count = count
        else:
            transformed = False

        return (POSITION, {
                    'transformed': transformed,
                    'full_text': '' if HIDE_WHEN_NONE and count == 0 else STRFORMAT.format(count),
                    'name': 'scratchpad-count', 
                    'cached_until': time.time() + CACHED_TIME,
                    })
