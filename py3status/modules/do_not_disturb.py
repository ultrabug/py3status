# -*- coding: utf-8 -*-
"""
A simple "Do Not Disturb" module that can turn on and off all system notifications.

A left mouse click will toggle the state of this module.

Configuration parameters:
    format_off: Display format when the "Do Not Disturb" mode is disabled.
        (default 'OFF')
    format_on: Display format when the "Do Not Disturb" mode is enabled.
        (default 'ON')
    notification_manager: The process name of your notification manager.
        (default 'dunst')
    refresh_interval: Refresh interval to use for killing notification manager process.
        (default 0.25)

Color options:
    color_bad: "Do Not Disturb" mode is enabled.
    color_good: "Do Not Disturb" mode is disabled.
"""

from time import sleep
from os import system
from threading import Thread, Event


class Py3status:
    """
    """

    # available configuration parameters
    format_off = 'OFF'
    format_on = 'ON'
    notification_manager = 'dunst'
    refresh_interval = 0.25

    def __init__(self):
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
        response = {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.format_on if self.running.is_set() else self.format_off,
            'color': self.py3.COLOR_BAD if self.running.is_set() else self.py3.COLOR_GOOD
        }
        return response

    def on_click(self, event):
        if event['button'] == 1:
            if self.running.is_set():
                self.running.clear()
            else:
                self.running.set()

    def kill(self):
        self.killed.set()
        self.running.set()  # ensure the thread won't hang


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
