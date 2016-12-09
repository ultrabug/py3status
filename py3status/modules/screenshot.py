# -*- coding: utf-8 -*-
"""
Take a screenshot and optionally upload it to your online server.

Display a 'SHOT' button in your i3bar allowing you to take a screenshot and
directly send (if wanted) the file to your online server.
When the screenshot has been taken, the file_name is shown. Right click to clean the name
when you don't need to see it anymore.

By default, this modules uses the 'gnome-screenshot' program to take the screenshot,
but this can be configured with the `screenshot_command` configuration parameter.

The upload can be configured with the `post_processing` parameter. It accepts the
following values:
    * `"scp"`: upload by `scp` protocol, needs `upload_server`, `upload_user` and
      `upload_path` to be configured.
    * `"lutim"`: upload on a [Lutim](https://framagit.org/luc/lutim) instance, needs
      `upload_server` to be configured (URL).
    * `"custom:path_to_script"`: specify a custom script which will be called after the
      screenshot has been taken and whose first argument will be the path to the
      screenshot.
    * `None`: No post processing. Same effect as parameter `push` set to `False`.

The `push` parameter is kept for compatibility reasons.

Configuration parameters:
    cache_timeout: how often to update in seconds (default 1)
    empty_text: text to display when there is nothing to show (default "SHOT")
    file_length: generated random file_name length (default 4)
    image_format: format of the screenshot (default 'jpg')
    logfile: path of the logfile, recommended if you use a image hoster, as you will keep
        the picture URL and the deletion URL (default None)
    open_webbrowser: when uploading to an image hoster, open the sent capture in the
        webbrowser (default True)
    post_processing: specify what to do with the screenshot (default 'scp')
    push: if you want to push your screenshot to your server (or whatever your optionnal
        custom script would do) (default True)
    random_name: generate a random filename for captures, else use date and time
        (default True)
    save_path: directory where to store your screenshots (default '~/Pictures/')
    screenshot_command: the command used to generate the screenshot
        (default 'gnome-screenshot -f')
    upload_path: the remote path where to push the screenshot (default '/files')
    upload_server: your server address (default 'puzzledge.org')
    upload_user: your ssh user (default 'erol')

Color options:
    color_done: Displayed color when full operation is over (default color_good)
    color_processing: color of the text during operation (default color_degraded)

Requires:
    requests: python module from pypi https://pypi.python.org/pypi/requests only required
        if you want to use a web API

@author Amaury Brisou <py3status AT puzzledge.org>, raspbeguy
"""
import os
import random
import string
import subprocess
import webbrowser
import datetime


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 1
    empty_text = "SHOT"
    file_length = 4
    image_format = 'jpg'
    logfile = None
    open_webbrowser = True
    post_processing = 'scp'
    push = True
    random_name = True
    save_path = '%s%s' % (os.environ['HOME'], '/Pictures/')
    screenshot_command = 'gnome-screenshot -f'
    upload_path = "/files"
    upload_server = 'puzzledge.org'
    upload_user = 'erol'

    def post_config_hook(self):
        self._reset_text()

    def on_click(self, event):
        button = event['button']
        if button == 1:
            self._full_text = "Shooting"
            self._color = self.py3.COLOR_PROCESSING or self.py3.COLOR_DEGRADED
            if self.random_name:
                file_name = "%s.%s" % (self._filename_generator(self.file_length),
                                       self.image_format)
            else:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                file_name = "%s.%s" % (timestamp, self.image_format)

            command = '%s %s/%s' % (self.screenshot_command,
                                    self.save_path,
                                    file_name)

            subprocess.call(command.split())
            logstring = None

            if self.push:
                self._full_text = "Sending"
                if self.post_processing == "scp":
                    logstring = self._push_scp(file_name)
                elif self.post_processing == "lutim":
                    logstring = self._push_lutim(file_name)
                elif self.post_processing is not None:
                    post_process = self.post_processing.split(sep=':', maxsplit=1)
                    if post_process[0] == "custom" and len(post_process) == 2:
                        logstring = self._push_custom(file_name, post_process[1])
            logline = "%s -> %s\n" % (file_name, logstring) if logstring else file_name

            if self.logfile:
                f = open(self.logfile, 'a')
                f.write(logline)
                f.close()

            self._full_text = file_name
            self._color = self.py3.COLOR_DONE or self.py3.COLOR_GOOD
            self.py3.prevent_refresh()
        else:
            self._reset_text()

    def _reset_text(self):
        self._full_text = self.empty_text
        self._color = None

    def _push_scp(self, file_name):
        if self.upload_server and self.upload_user and self.upload_path:
            dest = '%s@%s:%s' % (self.upload_user, self.upload_server, self.upload_path)
            command = 'scp %s/%s %s' % (self.save_path, file_name, dest)
            subprocess.call(command.split())
            logstring = "SCP to %s" % dest
            return logstring

    def _push_lutim(self, file_name):
        if self.upload_server:
            import requests
            r = requests.post(self.upload_server,
                              data={'format': 'json', 'delete-day': 1},
                              files={'file': open("%s/%s" % (self.save_path,
                                                             file_name), 'rb')},
                              )
            resp = r.json()["msg"]
            url = "%s/%s" % (self.upload_server, resp["short"])
            delurl = "%s/d/%s/%s" % (self.upload_server, resp["short"], resp["token"])
            try:
                webbrowser.open(url)
            except webbrowser.Error:
                pass
            logstring = "LUTIM to %s | deletion link %s" % (url, delurl)
            return logstring

    def _push_custom(self, file_name, script):
        command = script.split()
        command.append("%s/%s" % (self.save_path, file_name))
        code = subprocess.call(command)
        logstring = 'CUSTOM to "%s", returned code %d' % (script, code)
        return logstring

    def _filename_generator(self,
                            size=6,
                            chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def screenshot(self):
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self._full_text
        }

        if self._color is not None:
            response["color"] = self._color

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
