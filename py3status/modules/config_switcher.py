# -*- coding: utf-8 -*-
"""
Select config file py3status should use and switch between.

If more than one configuration file is supplied to py3status then this module
will let you select and switch between them.

Configuration parameters:
    button_change: button to select next config file.  None disables
        (default None)
    button_next: button to display next config file.  None disables
        (default None)
    button_previous: button to display previous config file.  None disables
        (default None)
    button_select: button to select displayed config file.  None disables
        (default 3)
    button_toggle: button to toggle open.  None disables
        (default 1)
    format: Display format to use
        (default '⚙[\?if=open  {file} {button_previous} {button_next}]')
    icon_next: icon to use for next button (default '→')
    icon_previous: icon to use for previous button (default '←')
    open: If the module is considered open (default False)

Format placeholders:
    {file} the name of the file
    {path} the path of the file
    {button_next} button to display next config file
    {button_previous} button to display previous config file

@author tobes
"""

import os.path


class Py3status:

    button_change = None
    button_next = None
    button_previous = None
    button_select = 3
    button_toggle = 1
    format = u'⚙[\?if=open  {file} {button_previous} {button_next}]'
    icon_next = u'→'
    icon_previous = u'←'
    open = False

    def __init__(self):
        pass

    def post_config_hook(self):
        py3status_config = self.py3.py3status_config()
        self.config_paths = py3status_config.get('i3status_config_paths', [])

        path = py3status_config.get('i3status_config_path')
        try:
            self.active = self.config_paths.index(path)
        except ValueError:
            self.active = 0

        self.buttons = {
            'button_previous': self.py3.composite_create({
                'full_text': self.icon_previous,
                'index': 'previous',
            }),
            'button_next': self.py3.composite_create({
                'full_text': self.icon_next,
                'index': 'next',
            }),
        }

    def config(self):
        path = self.py3.py3status_config().get('i3status_config_path')
        try:
            current = self.config_paths.index(path)
        except ValueError:
            current = 0

        if self.config_paths:
            self.active = self.active % len(self.config_paths)

            display_path = self.config_paths[self.active]
            display_file = os.path.basename(display_path)
            params = dict(
                path=display_path,
                file=display_file,
                open=self.open,
            )
            self.py3.log(params)
            params.update(self.buttons)
            self.py3.log(params)
        else:
            params = {}

        response = {
            'full_text': self.py3.safe_format(self.format, params),
            'cached_until': self.py3.CACHE_FOREVER,
        }

        if current == self.active:
            response['color'] = self.py3.COLOR_GOOD

        return response

    def on_click(self, event):
        # have we clicked on one of our 'buttons'?
        index = event.get('index')
        if index == 'previous':
            self.active -= 1
            return
        elif index == 'next':
            self.active += 1
            return

        # just a normal click
        button = event['button']
        if button == self.button_toggle:
            self.open = not self.open
        elif button == self.button_next:
            self.active += 1
        elif button == self.button_previous:
            self.active -= 1
        elif button == self.button_change:
            self.active += 1
            self.py3.set_config_file(self.config_paths[self.active])
            self.py3.prevent_refresh()
        elif button == self.button_select:
            self.py3.set_config_file(self.config_paths[self.active])
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
