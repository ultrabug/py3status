r"""
Turn on and off systemd suspend inhibitor.

Configuration parameters:
    format: display format for this module
        (default '[\?color=state SUSPEND [\?if=state OFF|ON]]')
    lock_types: specify state to inhibit, comma separated list
        https://www.freedesktop.org/wiki/Software/systemd/inhibit/
        (default ['handle-lid-switch', 'idle', 'sleep'])
    thresholds: specify color thresholds to use
        (default [(True, 'bad'), (False, 'good')])

Format placeholders:
    {state} systemd suspend inhibitor state, eg True, False

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author Cyrinux https://github.com/cyrinux
@license BSD

SAMPLE OUTPUT
[{'full_text': 'SUSPEND ON', 'color': '#00FF00'}]

off
[{'full_text': 'SUSPEND OFF', 'color': '#FF0000'}]
"""

from dbus import SystemBus
from os import close


STRING_DBUS_EXCEPTION = "DBUS error, systemd-logind not started?"
STRING_BAD_LOCK_TYPES = "DBUS error, bad lock types used"


class Py3status:
    """
    """

    # available configuration parameters
    format = r"[\?color=state SUSPEND [\?if=state OFF|ON]]"
    lock_types = ["handle-lid-switch", "idle", "sleep"]
    thresholds = [(True, "bad"), (False, "good")]

    def post_config_hook(self):
        try:
            self.login1 = SystemBus().get_object(
                "org.freedesktop.login1", "/org/freedesktop/login1"
            )
        except Exception:
            raise Exception(STRING_DBUS_EXCEPTION)
        self.lock = None
        self.lock_types = ":".join(self.lock_types)
        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def systemd_suspend_inhibitor(self):
        suspend_data = {"state": bool(self.lock)}

        for x in self.thresholds_init:
            if x in suspend_data:
                self.py3.threshold_get_color(suspend_data[x], x)

        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, suspend_data),
        }

    def on_click(self, event):
        if self.lock is None:
            self.lock = self.login1.Inhibit(
                self.lock_types,
                "Py3Status",
                "Systemd suspend inhibitor module",
                "block",
                dbus_interface="org.freedesktop.login1.Manager",
            ).take()
        else:
            close(self.lock)
            self.lock = None


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
