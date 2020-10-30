r"""
Turn on and off desktop notifications.

Configuration parameters:
    cache_timeout: refresh interval for this module; for xfce4-notifyd
        (default 30)
    format: display format for this module
        (default '{name} [\?color=state&show DND]')
    pause: specify whether to pause or kill processes; for dunst
        see `Dunst Miscellaneous` section for more information
        (default True)
    server: specify server to use, eg mako, dunst or xfce4-notifyd, otherwise auto
        (default None)
    state: specify state to use on startup, otherwise last
        False: disable Do Not Disturb on startup
        True: enable Do Not Disturb on startup
        last: toggle last known state on startup
        None: query current state from notification manager (doesn't work on dunst<1.5.0)
        (default 'last')
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (1, 'good')])

Format placeholders:
    {name} name, eg Mako, Dunst, Xfce4-notifyd
    {state} do not disturb state, eg 0, 1

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Dunst Miscellaneous:
    When paused, dunst will not display any notifications but keep all
    notifications in a queue. This can for example be wrapped around a screen
    locker (i3lock, slock) to prevent flickering of notifications through the
    lock and to read all missed notifications after returning to the computer.
    This means that by default (pause = False), all notifications sent while
    DND is active will NOT be queued and displayed when DND is deactivated.


Examples:
```
# display ON/OFF
do_not_disturb {
    format = '{name} [\?color=state [\?if=state  ON|OFF]]'
}

# display 1/0
do_not_disturb {
    format = '{name} [\?color=state {state}]'
}

# display DO NOT DISTURB/DISTURB
do_not_disturb {
    format = '[\?color=state [\?if=state DO NOT DISTURB|DISTURB]]'
    thresholds = [(0, "darkgray"), (1, "good")]
}
```

@author Maxim Baz https://github.com/maximbaz (dunst)
@author Robert Ricci https://github.com/ricci (xfce4-notifyd)
@author Cyrinux https://github.com/cyrinux (mako)
@license BSD

SAMPLE OUTPUT
[{'full_text': 'Dunst '}, {'color': '#00FF00', 'full_text': 'DND'}]

off
[{'full_text': 'Dunst '}, {'color': '#FF0000', 'full_text': 'DND'}]
"""

STRING_NOT_INSTALLED = "server `{}` not installed"
STRING_INVALID_SERVER = "invalid server `{}`"
STRING_INVALID_STATE = "invalid state `{}`"


class Notification:
    def __init__(self, parent):
        self.parent = parent
        self.setup(parent)

    def setup(self, parent):
        pass

    def get_state(self):
        return self.parent.state


class Dunst(Notification):
    """
    Dunst Notification.
    """

    def setup(self, parent):
        self.has_dunstctl = bool(self.parent.py3.check_commands(["dunstctl"]))

    def get_state(self):
        if self.has_dunstctl:
            state = self.parent.py3.command_output("dunstctl is-paused")
            return state.strip() == "true"
        else:
            return self.parent.state

    def toggle(self, state):
        if self.has_dunstctl:
            self.parent.py3.command_run(
                "dunstctl set-paused {}".format(str(state).lower())
            )
        elif state:
            # pause
            self.parent.py3.command_run("pkill -SIGUSR1 dunst")
        else:
            if self.parent.pause:
                # resume
                self.parent.py3.command_run("pkill -SIGUSR2 dunst")
            else:
                # delete all pending notifications and resume
                self.parent.py3.command_run("pkill -SIGTERM dunst")


class Mako(Notification):
    """
    Mako Notification.
    """

    def toggle(self, state):
        self.parent.py3.command_run("makoctl set invisible={}".format(int(state)))


class Xfce4_notifyd(Notification):
    """
    XFCE4 Notification.
    """

    def setup(self, parent):
        from dbus import Interface, SessionBus

        self.iface = Interface(
            SessionBus().get_object("org.xfce.Xfconf", "/org/xfce/Xfconf"),
            "org.xfce.Xfconf",
        )

    def get_state(self):
        return self.iface.GetProperty("xfce4-notifyd", "/do-not-disturb")

    def toggle(self, state):
        self.iface.SetProperty("xfce4-notifyd", "/do-not-disturb", state)


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 30
    format = r"{name} [\?color=state&show DND]"
    pause = True
    server = None
    state = "last"
    thresholds = [(0, "bad"), (1, "good")]

    def post_config_hook(self):
        servers = ["dunst", "mako", "xfce4-notifyd", None]
        if not self.server:
            for server in servers:
                if server:
                    try:
                        if self.py3.command_output(["pgrep", "-x", server]):
                            self.server = server
                            break
                    except self.py3.CommandError:
                        pass
            else:
                self.server = self.py3.check_commands(servers[:-1]) or "dunst"
        elif self.server not in servers:
            raise Exception(STRING_INVALID_SERVER.format(self.server))
        else:
            command = self.server.replace("notifyd", "notifyd-config")
            if not self.py3.check_commands(command):
                raise Exception(STRING_NOT_INSTALLED.format(command))

        if self.server == "dunst":
            self.backend = Dunst(self)
        elif self.server == "mako":
            self.backend = Mako(self)
        elif self.server == "xfce4-notifyd":
            self.backend = Xfce4_notifyd(self)

        if self.state is not None:
            if self.state == "last":
                self.state = self.py3.storage_get("state") or 0
            if self.state in [False, True]:
                self.backend.toggle(self.state)
            else:
                raise Exception(STRING_INVALID_STATE.format(self.state))
        elif self.server == "dunst" and not self.backend.has_dunstctl:
            raise Exception(STRING_INVALID_STATE.format(self.state))

        self.name = self.server.capitalize()
        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def do_not_disturb(self):
        self.state = self.backend.get_state()
        dnd_data = {"state": int(self.state), "name": self.name}

        for x in self.thresholds_init:
            if x in dnd_data:
                self.py3.threshold_get_color(dnd_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, dnd_data),
        }

    def on_click(self, event):
        self.state = not self.state
        self.py3.storage_set("state", self.state)
        self.backend.toggle(self.state)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
