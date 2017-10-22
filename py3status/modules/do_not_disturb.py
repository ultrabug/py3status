# -*- coding: utf-8 -*-
"""
Turn on and off dbus notifications.

A left mouse click will toggle the state of this module.

Configuration parameters:
    format: Display format for the "Do Not Disturb" module.
        (default '{state}')
    notification_manager: The process name of your notification manager.
        (default 'dunst')
    refresh_interval: Refresh interval to use for killing notification manager process.
        (default 0.25)
    state_off: Message when the "Do Not Disturb" mode is disabled.
        (default 'OFF')
    state_on: Message when the "Do Not Disturb" mode is enabled.
        (default 'ON')

Color options:
    color_bad: "Do Not Disturb" mode is enabled.
    color_good: "Do Not Disturb" mode is disabled.

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'OFF'}

off
{'color': '#FF0000', 'full_text': 'ON'}

@author Maxim Baz (https://github.com/maximbaz)
@license BSD
"""

from time import sleep
from os import system
from threading import Thread, Event


class Py3status:
    """
    """
    # available configuration parameters
    format = '{state}'
    notification_manager = 'dunst'
    refresh_interval = 0.25
    state_off = 'OFF'
    state_on = 'ON'

    def post_config_hook(self):
        self.is_on = False

        if not self._is_dunst():
            self._init_periodic_notifications_killer()

    def _is_dunst(self):
        return self.notification_manager == 'dunst'

    def _init_periodic_notifications_killer(self):
        self.running = Event()
        self.killed = Event()

        class MyThread(Thread):
            def run(this):
                while not self.killed.is_set():
                    if self.running.wait():
                        system("killall '{}'".format(self.notification_manager))
                        sleep(self.refresh_interval)

        MyThread().start()

    def do_not_disturb(self):
        state = self.state_on if self.is_on else self.state_off
        response = {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(self.format, {'state': state}),
            'color': self.py3.COLOR_BAD if self.is_on else self.py3.COLOR_GOOD
        }
        return response

    def on_click(self, event):
        if event['button'] == 1:
            self.is_on = not self.is_on
            if self._is_dunst():
                new_flag = '-SIGUSR1' if self.is_on else '-SIGTERM'
                system("killall {} dunst".format(new_flag))
            else:
                if self.is_on:
                    self.running.set()
                else:
                    self.running.clear()

    def kill(self):
        if not self._is_dunst():
            self.killed.set()
            self.running.set()  # ensure the thread won't hang


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
