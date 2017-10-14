# -*- coding: utf-8 -*-
"""
Show an indicator when YubiKey is waiting for a touch.

Configuration parameters:
    cache_timeout: How often to detect a pending touch request.
        (default 1)
    format: Display format for the module.
        (default '{state}')
    state_off: Message when the touch is not needed.
        (default '')
    state_on: Message when the YubiKey is waiting for a touch.
        (default 'Y')
    u2f_keys_path: Full path to u2f_keys if you want to monitor sudo access.
        (default '')

Color options:
    color_bad: Touch is needed.
    color_good: Touch is not needed.

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': ''}
{'color': '#FF0000', 'full_text': 'Y'}

Dependencies:
    gpg: to check for pending gpg access request
    inotify-simple: to check for pending sudo request
    subprocess32: if after all these years you are still using python2

@author Maxim Baz (https://github.com/maximbaz)
@license BSD
"""

import time
import os
import signal
import sys
import threading
import inotify_simple

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 1
    format = '{state}'
    state_off = ''
    state_on = 'Y'
    u2f_keys_path = ''

    def post_config_hook(self):
        self.killed = threading.Event()

        self.pending_gpg = False
        self.pending_sudo = False
        self.sudo_reset_timer = None

        class GpgThread(threading.Thread):
            def run(this):
                while not self.killed.is_set():
                    with subprocess.Popen(
                            'gpg --no-tty --card-status',
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            preexec_fn=os.setsid) as process:
                        try:
                            process.communicate(timeout=0.1)
                            self.pending_gpg = False
                        except subprocess.TimeoutExpired:
                            self.pending_gpg = True
                            os.killpg(process.pid, signal.SIGINT)
                            process.communicate()
                    time.sleep(self.cache_timeout)

        class SudoThread(threading.Thread):
            def run(this):
                inotify = inotify_simple.INotify()
                watch = inotify.add_watch(self.u2f_keys_path,
                                          inotify_simple.flags.ACCESS)
                while not self.killed.is_set():
                    for event in inotify.read():
                        self._restart_sudo_reset_timer()
                        self.pending_sudo = True
                inotify.rm_watch(watch)

        GpgThread().start()

        if self.u2f_keys_path != '':
            SudoThread().start()

    def _restart_sudo_reset_timer(self):
        def reset_pending_sudo():
            self.pending_sudo = False

        if self.sudo_reset_timer is not None:
            self.sudo_reset_timer.cancel()

        self.sudo_reset_timer = threading.Timer(5, reset_pending_sudo)
        self.sudo_reset_timer.start()

    def yubikey(self):
        pending_touch = self.pending_gpg or self.pending_sudo
        state = self.state_on if pending_touch else self.state_off
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'state': state}),
            'color': self.py3.COLOR_BAD
            if pending_touch else self.py3.COLOR_GOOD
        }
        return response

    def kill(self):
        self.killed.set()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
