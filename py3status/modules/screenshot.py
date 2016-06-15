# -*- coding: utf-8 -*-
"""
Take a screenshot and optionally upload it to your online server.

Display a 'SHOT' button in your i3bar allowing you to take a screenshot and
directly send (if wanted) the file to your online server.
When the screenshot has been taken, 'SHOT' is replaced by the file_name.

By default, this modules uses the 'gnome-screenshot' program to take the screenshot,
but this can be configured with the `screenshot_command` configuration parameter.

Configuration parameters:
    file_length: generated file_name length
    push: True/False if yo want to push your screenshot to your server
    save_path: Directory where to store your screenshots.
    screenshot_command: the command used to generate the screenshot
    upload_path: the remote path where to push the screenshot
    upload_server: your server address
    upload_user: your ssh user

@author Amaury Brisou <py3status AT puzzledge.org>
"""
import os
import random
import string
import subprocess
import time


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

    def on_click(self, i3s_output_list, i3s_config, event):

        file_name = self._filename_generator(self.file_length)

        command = '%s %s/%s%s' % (self.screenshot_command, self.save_path,
                                  file_name, '.jpg')

        subprocess.Popen(command.split())

        self.full_text = '%s%s' % (file_name, '.jpg')

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

    def screenshot(self, i3s_output_list, i3s_config):
        if self.full_text == '':
            self.full_text = 'SHOT'

        response = {
            'cached_until': time.time() + self.cache_timeout,
            'color': i3s_config['color_good'],
            'full_text': self.full_text
        }
        return response


if __name__ == "__main__":

    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00',
    }
    while True:
        print(x.screenshot([], config))
        sleep(1)
