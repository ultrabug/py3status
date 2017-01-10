# -*- coding: utf-8 -*-
"""
Take a screenshot and optionally upload it to your online server.

Display a 'SHOT' button in your i3bar allowing you to take a screenshot and
directly send (if wanted) the file to your online server.
When the screenshot has been taken, 'SHOT' is replaced by the file_name.

By default, this modules uses the 'gnome-screenshot' program to take the screenshot,
but this can be configured with the `screenshot_command` configuration parameter.

Configuration parameters:
    cache_timeout: how often to update in seconds (default 5)
    file_length: generated file_name length (default 4)
    push: True/False if you want to push your screenshot to your server
        (default True)
    save_path: Directory where to store your screenshots. (default '~/Pictures/')
    screenshot_command: the command used to generate the screenshot
        (default 'gnome-screenshot -f')
    upload_path: the remote path where to push the screenshot (default '/files')
    upload_server: your server address (default 'puzzledge.org')
    upload_user: your ssh user (default 'erol')

Color options:
    color_good: Displayed color

@author Amaury Brisou <py3status AT puzzledge.org>
"""
import os
import random
import string
import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    file_length = 4
    push = True
    save_path = '%s%s' % (os.environ['HOME'], '/Pictures/')
    screenshot_command = 'gnome-screenshot -f'
    upload_path = "/files"
    upload_server = 'puzzledge.org'
    upload_user = 'erol'

    def __init__(self):
        self.full_text = ''

    def on_click(self, event):

        buttons = (None, 'left', 'middle', 'right', 'up', 'down')
        try:
            button = buttons[event['button']]
        except IndexError:
            return

        if button in ('middle','right'):
            self.full_text = self.format

        if button == 'left':

            file_name = self._filename_generator(self.file_length)

        self.full_text = '%s%s' % (file_name, '.jpg')

            subprocess.Popen(command.split())

            self.full_text = '%s%s' % (file_name, '.jpg')
            self.full_text = self.py3.safe_format(self.format_screenshot,
                                                 {'filename': self.full_text})

            if (self.push and self.upload_server and self.upload_user and
                    self.upload_path):
                command = 'scp %s/%s%s %s@%s:%s' % (
                    self.save_path, file_name, '.jpg', self.upload_user,
                    self.upload_server, self.upload_path)
                subprocess.Popen(command.split())

    def _filename_generator(self,
                            size=6,
                            chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def screenshot(self):
        if self.full_text == '':
            self.full_text = 'SHOT'

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': self.py3.COLOR_GOOD,
            'full_text': self.full_text
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
