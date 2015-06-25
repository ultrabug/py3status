# -*- coding: utf-8 -*-
"""
Display static text

Display static text given by "text" parameter

Configuration parameters:
    - text          : text that should be printed
    - separator     : whether the separator is shown or not (True or False)
    - color         : color of printed text
    - on_click      : read goo.gl/u10n0x

@author frimdo ztracenastopa@centrum.cz
"""
 
class Py3status:
    color = None
    text = ""
    separator = True
 
    def static_string(self, i3s_output_list, i3s_config):
 
        response = {
            'full_text': self.text,
            'color': self.color,
            'separator': self.separator
            }
 
        return response
 
if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    print(x.static_string([], config))

