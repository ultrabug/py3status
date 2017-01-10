# -*- coding: utf-8 -*-
"""
Take a screenshot and optionally upload it to your online server.

Display a 'SHOT' button in your i3bar allowing you to take a screenshot and
directly send (if wanted) the file to your online server.
When the screenshot has been taken, 'SHOT' is replaced by the random_filename.

By default, this modules uses the 'gnome-screenshot' program to take the screenshot,
but this can be configured with the `command` configuration parameter.

Configuration parameters:
    cache_timeout: how often to update in seconds (default 5)
    command: the command used to generate the screenshot (default 'scrot')
    file_length: generated random_filename length (default 4)
    format: format to display (default '{format_ss}📷')
    format_ss: format to display (default '{ss} ')
    path: Directory where to store your screenshots (default '~/Pictures/')
    remote_path: the remote path where to push the screenshot (default '/files')
    remote_push: True/False if you want to push your screenshot to your server (default False)
    remote_server: your server address (default 'puzzledge.org')
    remote_user: your ssh user (default 'erol')

Placeholder for format:
    {format_ss} format to display (default '{format_ss} 📷 Screenshot')

Placeholder for format_ss:
    {ss} screenshot filename (default '({ss})')

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
    command = 'scrot'
    file_length = 4
    format = u'{format_ss}📷'
    format_ss = u'{ss} '
    path = '%s%s' % (os.environ['HOME'], '/Pictures/')
    remote_path = "/files"
    remote_push = False
    remote_server = 'puzzledge.org'
    remote_user = 'erol'

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'screenshot_command',
                    'new': 'command',
                    'msg': 'obsolete parameter use `command`'
                },
                {
                    'param': 'save_path',
                    'new': 'path',
                    'msg': 'obsolete parameter use `path`'
                },
                {
                    'param': 'upload_path',
                    'new': 'remote_path',
                    'msg': 'obsolete parameter use `remote_path`'
                },
                {
                    'param': 'push',
                    'new': 'remote_push',
                    'msg': 'obsolete parameter use `remote_push`'
                },
                {
                    'param': 'upload_server',
                    'new': 'remote_server',
                    'msg': 'obsolete parameter use `remote_server`'
                },
                {
                    'param': 'upload_user',
                    'new': 'remote_user',
                    'msg': 'obsolete parameter use `remote_user`'
                },
            ],
        }

    def __init__(self):
        self.full_text = ''

    def on_click(self, event):

        buttons = (None, 'left', 'middle', 'right', 'up', 'down')
        try:
            button = buttons[event['button']]
        except IndexError:
            return

        if button in ('middle', 'right'):
            self.full_text = self.py3.safe_format(self.format, {'format_ss': ''})

        if button == 'left':

            random_filename = self._filename_generator(self.file_length)
            command = '%s %s/%s%s' % (self.command, self.path, random_filename, '.jpg')
            subprocess.Popen(command.split())

            self.full_text = '%s%s' % (random_filename, '.jpg')
            self.full_text = self.py3.safe_format(self.format_ss, {'ss': self.full_text})
            self.full_text = self.py3.safe_format(self.format, {'format_ss': self.full_text})

            if (self.remote_push and self.remote_server and self.remote_user and self.remote_path):
                command = 'scp %s/%s%s %s@%s:%s' % (
                    self.path, random_filename, '.jpg', self.remote_user,
                    self.remote_server, self.remote_path)
                subprocess.Popen(command.split())

    def _filename_generator(self, size=6, chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def screenshot(self):
        if self.full_text == '':
            self.full_text = self.py3.safe_format(self.format_ss, {'ss': ''})
            self.full_text = self.py3.safe_format(self.format, {'format_ss': ''})

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.full_text
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
