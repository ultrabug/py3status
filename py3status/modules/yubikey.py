# -*- coding: utf-8 -*-
"""
Show an indicator when YubiKey is waiting for a touch.

Configuration parameters:
    cache_timeout: How often to detect a pending touch request.
        (default 1)
    format: Display format for the module.
        (default '\?if=is_waiting YubiKey')
    u2f_keys_path: Full path to u2f_keys if you want to monitor sudo access.
        (default '~/.config/Yubico/u2f_keys')

Control placeholders:
    {is_waiting} a boolean indicating whether YubiKey is waiting for a touch.

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'YubiKey'}

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
    format = '\?if=is_waiting YubiKey'
    u2f_keys_path = '~/.config/Yubico/u2f_keys'

    def post_config_hook(self):
        self.u2f_keys_path = os.path.expanduser(self.u2f_keys_path)

        self.killed = threading.Event()

        self.pending_gpg = False
        self.pending_sudo = False

        class GpgThread(threading.Thread):
            def _check_card_status(this):
                return subprocess.Popen(
                    'gpg --no-tty --card-status',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid)

            def run(this):
                inotify = inotify_simple.INotify()
                gpg_watch = inotify.add_watch(
                    os.path.expanduser('~/.gnupg/pubring.kbx'),
                    inotify_simple.flags.OPEN)
                ssh_watch = inotify.add_watch(
                    os.path.expanduser('~/.ssh/known_hosts'),
                    inotify_simple.flags.OPEN)

                while not self.killed.is_set():
                    for event in inotify.read():
                        # e.g. ssh doesn't start immediately, try several seconds to be sure
                        for i in range(20):
                            with this._check_card_status() as check:
                                try:
                                    # if this doesn't return very quickly, touch is pending
                                    check.communicate(timeout=0.1)
                                    time.sleep(0.25)
                                except subprocess.TimeoutExpired:
                                    self.pending_gpg = True
                                    os.killpg(check.pid, signal.SIGINT)
                                    check.communicate()
                                    # wait until device is touched
                                    with this._check_card_status() as wait:
                                        wait.communicate()
                                        self.pending_gpg = False
                                        break

                        # ignore all events caused by operations above
                        for _ in inotify.read():
                            pass

                inotify.rm_watch(gpg_watch)
                inotify.rm_watch(ssh_watch)

        class SudoThread(threading.Thread):
            def _restart_sudo_reset_timer(this):
                def reset_pending_sudo():
                    self.pending_sudo = False

                if this.sudo_reset_timer is not None:
                    this.sudo_reset_timer.cancel()

                this.sudo_reset_timer = threading.Timer(5, reset_pending_sudo)
                this.sudo_reset_timer.start()

            def run(this):
                this.sudo_reset_timer = None

                inotify = inotify_simple.INotify()
                watch = inotify.add_watch(self.u2f_keys_path,
                                          inotify_simple.flags.ACCESS)

                while not self.killed.is_set():
                    for event in inotify.read():
                        this._restart_sudo_reset_timer()
                        self.pending_sudo = True

                inotify.rm_watch(watch)

        GpgThread().start()

        if os.path.isfile(self.u2f_keys_path):
            SudoThread().start()

    def yubikey(self):
        is_waiting = self.pending_gpg or self.pending_sudo
        format_params = {'is_waiting': is_waiting}
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, format_params),
        }
        if is_waiting:
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
