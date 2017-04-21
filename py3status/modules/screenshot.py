# -*- coding: utf-8 -*-
"""
Take screenshots and upload them to a given server.

Display CAMERA icon in your i3bar allowing you to take a screenshot. When
a screenshot has been taken, random generated filename will appear. If
configured correctly, you can upload the file to your server too.

By default, this modules looks for one of the screenshots commands (in that
order) to take the screenshot with. This can be configured directly instead
by using the `command` configuration parameter.

Configuration parameters:
    cache_timeout: how often to update in seconds (default 5)
    command: command used to take the screenshot (default None)
    file_length: generated random_filename length (default 4)
    format: display format for screenshot (default '{format_ss}📷')
    format_ss: format to display filename (default '{ss} ')
    path: directory to store the screenshots (default '~/Pictures/')
    remote_path: the remote path where to push the screenshot (default '/files')
    remote_push: True/False if you want to push your screenshot to your server (default False)
    remote_server: your server address (default 'puzzledge.org')
    remote_user: your ssh user (default 'erol')

Placeholder for format:
    {format_ss} display screenshot filename (default '{format_ss} 📷')

Placeholder for format_ss:
    {ss} screenshot filename (default '({ss})')

@author Amaury Brisou <py3status AT puzzledge.org>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'SHOT'}
"""
import os
import random
import string
import subprocess

COMMANDS = {
    'maim': 'maim',
    'scrot': 'scrot',
    'import': 'import -window root',
    'gnome-screenshot': 'gnome-screenshot -f',
}


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    command = None
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

    def post_config_hook(self):
        self.full_text = ''
        if not self.command:
            cmd = self.py3.check_commands(COMMANDS.keys())
            if cmd:
                self.command = COMMANDS[cmd]
        self.py3.log('selected: %s' % self.command)

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

            if (self.remote_push and self.remote_server
                    and self.remote_user and self.remote_path):

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
