# -*- coding: utf-8 -*-
"""
Display static text.

Configuration parameters:
    - color         : color of printed text
    - format        : text that should be printed
    - separator     : whether the separator is shown or not (true or false)

@author frimdo ztracenastopa@centrum.cz
"""

from time import time


class Py3status:
    """
    """
    # available configuration parameters
    color = None
    format = ''
    separator = True

    def static_string(self, i3s_output_list, i3s_config):
        response = {
            'cached_until': time() + 60,
            'color': self.color,
            'full_text': self.format,
            'separator': self.separator
        }
        return response


if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    print(x.static_string([], config))
