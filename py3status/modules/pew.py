# -*- coding: utf-8 -*-
"""
Display Pew! notifications on the bar.

Configuration parameters:
    format: display format for this module (default "[{summary}][\|{body}]")
    timeout: notification timeout for this module (default 10)

Format placeholders:
    {name} application name, eg Pidgin, Thunderbird, notify-send
    {summary} notification summary, eg You received 1 new message
    {body} notification body, eg Cops just left. You can come in.

@author lasers

Examples:
```
# show notification bell
pew {
    format = '[\?if=summary ]'
}

# customize notification
pew {
    format = '[\?color=red {summary}][\?color=white  {body}]'
    allow_urgent = False
}

# customize per client notifications
pew {
    allow_urgent = False
    format = '['

    # Pidgin
    format += '[\?if=name=Pidgin [\?color=violet  {name}]'
    format += '[\?color=red  {summary}][\?color=white  {body}]]'

    # Thunderbird
    format += '[\?if=name=Thunderbird [\?color=skyblue  {name}]'
    format += '[\?color=deepskyblue {summary}][\?color=white  {body}]]'

    # Others
    format += '|[\?color=orange {summary}][\?color=yellow  {body}]]'
}
```

SAMPLE OUTPUT
[{'full_text': 'Pew!', 'urgent': True}]

pidgin_notification
[
    {'full_text': 'User says: ', 'color': '#ff0000'}, {'full_text': '>_>'},
]

thunderbird_notification
[
    {'full_text': 'You received 1 new message ', 'color': '#00bfff'},
    {'full_text': 'Hi!'},
]
"""

try:
    from html import unescape  # python3 only
except ImportError:
    pass
else:
    from dbus import SessionBus
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib
    from threading import Thread
    from time import sleep

PARAM_STRING = "eavesdrop=true, member='Notify', "
PARAM_STRING += "interface='org.freedesktop.Notifications'"


class Py3status:
    """
    """

    # available configuration parameters
    format = "[{summary}][\|{body}]"
    timeout = 10

    def post_config_hook(self):
        if self.py3.is_python_2():
            raise Exception('Python2 not supported')
        self._hide_notification()
        t = Thread(target=self._start_loop)
        t.daemon = True
        t.start()

    def _start_loop(self):
        DBusGMainLoop(set_as_default=True)
        bus = SessionBus()
        # TODO: replace eavesdropping with BecomeMonitor
        bus.add_match_string_non_blocking(PARAM_STRING)
        bus.add_message_filter(self._show_notification)
        self.mainloop = GLib.MainLoop()
        self.mainloop.run()

    def _hide_notification(self):
        self.pew_data = {}

    def _show_notification(self, bus, notification):
        notification = notification.get_args_list()[:5]
        self.pew_data = {
            "name": notification[0],
            "summary": unescape(" ".join(notification[3].splitlines())),
            "body": unescape(" ".join(notification[4].splitlines())),
        }
        self.py3.update()

        sleep(self.timeout)
        self._hide_notification()
        self.py3.update()

    def pew(self):
        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, self.pew_data),
            "urgent": True,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
