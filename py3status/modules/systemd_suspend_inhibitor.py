# -*- coding: utf-8 -*-
"""
Turn on and off systemd suspend inhibitor.

Configuration parameters:
    cache_timeout: refresh interval for this module; for xfce4-notifyd
        (default 30)
    format: display format for this module
        (default '{ [\?color=state&show SUSPEND [\?if=state OFF|ON]]')
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (1, 'good')])

Format placeholders:
    {state} systemd suspend inhibitor state, eg True, False

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder


Examples:
```
# display SUSPEND ON/OFF
systemd_suspend_inhibitor {
    format = '[\?color=state&show SUSPEND [\?if=state OFF|ON]]'
    thresholds = [(True, "bad"), (False, "good")]
}
```

"""

from os import close


class Inhibit:
    """
    """
    def __init__(self):
        from dbus import SystemBus
        self.bus = SystemBus()
        self.fd = None
        self.proxy = self.bus.get_object("org.freedesktop.login1",
                                         "/org/freedesktop/login1")

    def get_state(self):
        return True if self.fd else False

    def toggle(self):
        if self.fd is None:
            self.fd = self.proxy.Inhibit(
                "sleep",
                "Py3Status",
                "systemd suspend inhibitor module",
                "block",
                dbus_interface="org.freedesktop.login1.Manager").take()
        else:
            close(self.fd)
            self.fd = None


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 30
    format = "[\?color=state&show SUSPEND [\?if=state OFF|ON]]"
    thresholds = [(True, "bad"), (False, "good")]

    def post_config_hook(self):
        self.inhibit = Inhibit()
        self.state = None
        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def systemd_suspend_inhibitor(self):
        self.state = self.inhibit.get_state()
        data = {"state": int(self.state)}

        for x in self.thresholds_init:
            if x in data:
                self.py3.threshold_get_color(data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, data),
        }

    def on_click(self, event):
        self.inhibit.toggle()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
