# -*- coding: utf-8 -*-
"""
Take screenshots and upload them to a given server.

Configuration parameters:
    file_length: generated file_name length (default 4)
    format: display format for this module
        (default '\?color=good [{basename}|\?show SHOT]')
    save_path: Directory where to store your screenshots (default '~/Pictures')
    screenshot_command: the command used to generate the screenshot
        (default 'gnome-screenshot -f')
    upload_path: the remote path where to push the screenshot (default None)
    upload_server: your server address (default None)
    upload_user: your ssh user (default None)

Format placeholders:
    {basename} generated basename, eg qs60.jpg

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

basename
{'color': '#00FF00', 'full_text': 'qs60.jpg'}
"""

import os
import random
import string


class Py3status:
    """
    """

    # available configuration parameters
    file_length = 4
    format = "\?color=good [{basename}|\?show SHOT]"
    save_path = "~/Pictures"
    screenshot_command = "gnome-screenshot -f"
    upload_path = None
    upload_server = None
    upload_user = None

    class Meta:
        deprecated = {
            "remove": [
                {"param": "push", "msg": "obsolete"},
                {"param": "cache_timeout", "msg": "obsolete"},
            ]
        }

    def post_config_hook(self):
        self.shot_data = {}
        self.save_path = os.path.expanduser(self.save_path)
        self.chars = string.ascii_lowercase + string.digits

    def _generator(self, size=6):
        return "".join(random.choice(self.chars) for _ in range(size))

    def screenshot(self):
        return {
            "cached_until": self.py3.time_in(self.py3.CACHE_FOREVER),
            "full_text": self.py3.safe_format(self.format, self.shot_data),
        }

    def on_click(self, event):
        basename = self._generator(self.file_length) + ".jpg"
        pathname = os.path.join(self.save_path, basename)
        self.shot_data["basename"] = basename

        self.py3.command_run(" ".join([self.screenshot_command, pathname]))

        if self.upload_server and self.upload_user and self.upload_path:
            self.py3.command_run(
                "scp {} {}@{}:{}".format(
                    pathname, self.upload_user, self.upload_server, self.upload_path
                )
            )


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
