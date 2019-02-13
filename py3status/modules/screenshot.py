# -*- coding: utf-8 -*-
"""
Take screenshots and upload them to a given server.

Display a 'SHOT' button in your i3bar allowing you to take a screenshot and
directly send (if wanted) the file to your online server.
When the screenshot has been taken, 'SHOT' is replaced by the file_name.

By default, this modules uses the 'gnome-screenshot' program to take the screenshot,
but this can be configured with the `screenshot_command` configuration parameter.

Configuration parameters:
    cache_timeout: how often to update in seconds (default 5)
    file_length: generated file_name length (default 4)
    save_path: Directory where to store your screenshots. (default '~/Pictures/')
    screenshot_command: the command used to generate the screenshot
        (default 'gnome-screenshot -f')
    upload_path: the remote path where to push the screenshot (default None)
    upload_server: your server address (default None)
    upload_user: your ssh user (default None)

Color options:
    color_good: Displayed color

Examples:
```
# push screenshots to a server
screenshot {
    save_path = "~/Pictures/"
    upload_user = "erol"
    upload_server = "puzzledge.org"
    upload_path = "/files"

    # scp $HOME/Pictures/$UUID.jpg erol@puzzledge.org:/files
}
```

@author Amaury Brisou <py3status AT puzzledge.org>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'SHOT'}
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
    save_path = "~/Pictures/"
    screenshot_command = "gnome-screenshot -f"
    upload_path = None
    upload_server = None
    upload_user = None

    class Meta:
        deprecated = {"remove": [{"param": "push", "msg": "obsolete"}]}

    def post_config_hook(self):
        self.save_path = os.path.expanduser(self.save_path)
        self.full_text = ""

    def _filename_generator(self, size=6, chars=string.ascii_lowercase + string.digits):
        return "".join(random.choice(chars) for _ in range(size))

    def screenshot(self):
        if self.full_text == "":
            self.full_text = "SHOT"

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": self.py3.COLOR_GOOD,
            "full_text": self.full_text,
        }
        return response

    def on_click(self, event):
        file_name = self._filename_generator(self.file_length) + ".jpg"
        file_path = os.path.join(self.save_path, file_name)
        self.full_text = file_name

        command = "{} {}".format(self.screenshot_command, file_path)
        subprocess.Popen(command.split())

        if self.upload_server and self.upload_user and self.upload_path:
            command = "scp {} {}@{}:{}".format(
                file_path, self.upload_user, self.upload_server, self.upload_path
            )
            subprocess.Popen(command.split())


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
