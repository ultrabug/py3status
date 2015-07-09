# -*- coding: utf-8 -*-
"""
Display static text

Display static text given by "format" parameter

Configuration parameters:
    - text          : text that should be printed
    - separator     : whether the separator is shown or not (True or False)
    - format        : text that should be printed
    - color         : color of printed text
    - on_click      : read goo.gl/u10n0x

@author frimdo ztracenastopa@centrum.cz
"""


class Py3status:
    color = None
    format = ''
    separator = True

    def static_string(self, i3s_output_list, i3s_config):

        response = {
            'full_text': self.format,
            'color': self.color,
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
