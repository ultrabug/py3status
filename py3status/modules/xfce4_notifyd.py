# -*- coding: utf-8 -*-
"""
Display and toggle the DND (do-not-disturb) status of xfce4-notifyd

Toggles DND status on click

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    dnd_off: status string when DND is off (default 'Off')
    dnd_on: status string when DND is on (default 'On')
    format: display format for this module (default 'DND: {status}')

Format of status string placeholders:
    {status} replaced with dnd_off when DND is off, dnd_on when it is on

Color options:
    color_good: DND off
    color_bad: DND on

Examples:
```
xfce4_notifyd {
     dnd_off = "🙉"
     dnd_on = "🙈"
}
```

Requires:
    dbus: python bindings for dbus

@author Robert Ricci <robert.ricci@gmail.com>
@license BSD
"""

import dbus

class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    dnd_off = "Off"
    dnd_on = "On"
    format = 'DND: {status}'

    # not intended to be overriden
    bus_name = 'org.xfce.Xfconf'
    channel = 'xfce4-notifyd'
    interface_name = 'org.xfce.Xfconf'
    object_path = '/org/xfce/Xfconf'
    setting = '/do-not-disturb'

    def post_config_hook(self):
        self.session_bus = dbus.SessionBus()
        self.dnd_object = self.session_bus.get_object(self.bus_name, self.object_path) 
        self.interface = dbus.Interface(self.dnd_object, self.interface_name)

    def xfce4_notifyd(self):

        self.status = self.dnd_object.GetProperty(self.channel, self.setting)

        status = self.dnd_off
        color = self.py3.COLOR_GOOD
        if self.status:
            color = self.py3.COLOR_BAD
            status = self.dnd_on

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
            'full_text': self.py3.safe_format(
                self.format, {'status': status})
        }

    def on_click(self, event):
        """
        Toggle status
        """
        new_status = 1
        if self.status:
            new_status = 0

        self.interface.SetProperty(self.channel, self.setting, new_status)

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
