# -*- coding: utf-8 -*-
"""
Display systemd1 unit properties of a service.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module
        *(default '{Id} [\?if=LoadState=not-found&color=degraded '
        '{LoadState}|[\?color=ActiveState {ActiveState}]]')*
    thresholds: specify color thresholds to use
        (default [('inactive', 'bad'), ('active', 'good')])
    unit: specify a systemd1 unit to use (default 'sshd.service')

Format placeholders:
    {ActiveState}   eg inactive, active
    {Description}   eg OpenSSH Daemon
    {Id}            eg sshd.service
    {LoadState}     eg loaded, not-found

    Use...
    ```
    dbus-send --print-reply --system --type=method_call \
        --dest=org.freedesktop.systemd1 \
        /org/freedesktop/systemd1/unit/sshd_2eservice \
        org.freedesktop.DBus.Properties.GetAll string:''
    ```
    for a full list of systemd1 `sshd.service` unit properties to use.
    Not all of systemd1 unit properties will be supported or usable. For
    different systemd1 units, you can find out with d-feet or other tools.

Color options:
    color_good: systemd1 unit active
    color_bad: systemd1 unit inactive
    color_degraded: systemd1 unit not-found

Examples:
```
# show the status of vpn service
# left click to start, right click to stop
systemd vpn {
    unit = 'vpn.service'
    on_click 1 = 'exec sudo systemctl start vpn'
    on_click 3 = 'exec sudo systemctl stop vpn'
}
```

Examples:
```
# legacy theme
systemd {
    format = '[\?if=LoadState=not-found&color=degraded {Id} {LoadState}'
    format += '|[\?color=ActiveState {Id} {ActiveState}]]'
}

# replace sshd.service with sshd
systemd {
    # custom name or icon
    format = 'sshd [\?if=LoadState=not-found&color=degraded {LoadState}'
    format += '|[\?color=ActiveState {ActiveState}]]'
        OR
    # cut off the length
    format = '[\?max_length=-8 {Id}] [\?if=LoadState=not-found&color=degraded'
    format += ' {LoadState}|[\?color=ActiveState {ActiveState}]]'
}

# show if inactive or active
systemd {
    # show if inactive
    format = '[\?if=LoadState=not-found {Id} [\?color=degraded {LoadState}]]'
    format += '[\?if=ActiveState=inactive {Id} [\?color=bad {ActiveState}]]'
        OR
    # show if active
    format = '[\?if=LoadState=not-found {Id} [\?color=degraded {LoadState}]]'
    format += '[\?if=ActiveState=active {Id} [\?color=good {ActiveState}]]'
}

# show if active and disabled or inactive and enabled
systemd {
    format = '[\?if=LoadState=not-found {Id} [\?color=degraded {LoadState}]]'
    format += '[\?if=ActiveState=active [\?if=UnitFileState=disabled '
    format += '{Id} [\?color=ActiveState {ActiveState}]]]'
    format += '[\?if=ActiveState=inactive [\?if=UnitFileState=enabled '
    format += '{Id} [\?color=ActiveState {ActiveState}]]]'
}
```

@author Adrian Lopez <adrianlzt@gmail.com>
@license BSD

SAMPLE OUTPUT
[
    {'full_text': 'sshd.service '},
    {'color': '#00FF00', 'full_text': 'active'}
]

inactive
[
    {'full_text': 'sshd.service '},
    {'color': '#FF0000', 'full_text': 'inactive'}
]

not-found
[
    {'full_text': 'sshd.service '},
    {'color': '#FFFF00', 'full_text': 'not-found'}
]

"""

import dbus

SYSTEMD1 = "org.freedesktop.systemd1"
UNIT = "org.freedesktop.systemd1.Unit"
PROP = "org.freedesktop.DBus.Properties"
MANAGER = "org.freedesktop.systemd1.Manager"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = (
        "{Id} [\?if=LoadState=not-found&color=degraded {LoadState}"
        "|[\?color=ActiveState {ActiveState}]]"
    )
    thresholds = [("inactive", "bad"), ("active", "good")]
    unit = "sshd.service"

    class Meta:
        deprecated = {
            "rename_placeholder": [
                {
                    "placeholder": "status",
                    "new": "ActiveState",
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        self.placeholders = self.py3.get_placeholders_list(self.format)
        self.thresholds_init = self.py3.get_color_names_list(self.format)

        bus = dbus.SystemBus()
        systemd = bus.get_object(SYSTEMD1, "/org/freedesktop/systemd1")
        manager = dbus.Interface(systemd, dbus_interface=MANAGER)
        proxy = bus.get_object(SYSTEMD1, manager.LoadUnit(self.unit))
        self.systemd_unit = dbus.Interface(proxy, dbus_interface=UNIT)

    def systemd(self):
        systemd_data = self.systemd_unit.GetAll(UNIT, dbus_interface=PROP)

        for x in self.placeholders:
            if x in systemd_data:
                if isinstance(systemd_data[x], (list, tuple)):
                    systemd_data[x] = ", ".join(systemd_data[x])

        for x in self.thresholds_init:
            if x in systemd_data:
                self.py3.threshold_get_color(systemd_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, systemd_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
