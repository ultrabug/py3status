# -*- coding: utf-8 -*-
"""
Show an indicator when YubiKey is waiting for a touch.

Configuration parameters:
    format: Display format for the module.
        (default '[YubiKey[\?if=is_gpg ][\?if=is_u2f ]]')
    socket_path: A path to the yubikey-touch-detector socket file.
        (default '$XDG_RUNTIME_DIR/yubikey-touch-detector.socket')

Control placeholders:
    {is_gpg} a boolean, True if YubiKey is waiting for a touch due to a gpg operation.
    {is_u2f} a boolean, True if YubiKey is waiting for a touch due to a pam-u2f request.

SAMPLE OUTPUT
{'full_text': 'YubiKey', 'urgent': True}

Requires:
    github.com/maximbaz/yubikey-touch-detector: tool to detect when YubiKey is waiting for a touch

@author Maxim Baz (https://github.com/maximbaz)
@license BSD
"""

import time
import os
import socket
import threading


class YubikeyTouchDetectorListener(threading.Thread):
    """
    A thread watchng if YubiKey is waiting for a touch
    """

    def __init__(self, parent):
        super(YubikeyTouchDetectorListener, self).__init__()
        self.parent = parent

    def _connect_socket(self):
        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(self.parent.socket_path)
        except:
            self.socket = None

    def run(self):
        while not self.parent.killed.is_set():
            self._connect_socket()

            if self.socket is None:
                # Socket is not available, try again soon
                time.sleep(60)
                continue

            while not self.parent.killed.is_set():
                data = self.socket.recv(5)
                if not data:
                    # Connection dropped, need to reconnect
                    break
                elif data == b"GPG_1":
                    self.parent.is_waiting_gpg = True
                elif data == b"GPG_0":
                    self.parent.is_waiting_gpg = False
                elif data == b"U2F_1":
                    self.parent.is_waiting_u2f = True
                elif data == b"U2F_0":
                    self.parent.is_waiting_u2f = False
                self.parent.py3.update()


class Py3status:
    """
    """
    # available configuration parameters
    format = '[YubiKey[\?if=is_gpg ][\?if=is_u2f ]]'
    socket_path = '$XDG_RUNTIME_DIR/yubikey-touch-detector.socket'

    def post_config_hook(self):
        self.socket_path = os.path.expanduser(self.socket_path)
        self.socket_path = os.path.expandvars(self.socket_path)

        self.killed = threading.Event()

        self.is_waiting_gpg = False
        self.is_waiting_u2f = False

        YubikeyTouchDetectorListener(self).start()

    def yubikey(self):
        format_params = {
            'is_gpg': self.is_waiting_gpg,
            'is_u2f': self.is_waiting_u2f,
        }
        response = {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(self.format, format_params),
        }
        if self.is_waiting_gpg or self.is_waiting_u2f:
            response['urgent'] = True
        return response

    def kill(self):
        self.killed.set()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
