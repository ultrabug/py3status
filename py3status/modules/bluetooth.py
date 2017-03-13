# -*- coding: utf-8 -*-
"""
Display bluetooth status.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    device_separator: the separator char between devices (only if more than one
        device) (default '|')
    format: format when there is a connected device (default '{name}')
    format_no_conn: format when there is no connected device (default 'OFF')
    format_no_conn_prefix: prefix when there is no connected device
        (default 'BT: ')
    format_prefix: prefix when there is a connected device (default 'BT: ')

Format placeholders:
    {name} device name
    {mac} device MAC address

Color options:
    color_bad: Connection on
    color_good: Connection off

@author jmdana <https://github.com/jmdana>
@license GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'BT: Microsoft Bluetooth Notebook Mouse 5000'}

off
{'color': '#FF0000', 'full_text': u'BT: OFF'}
"""

import dbus


def get_connected_devices():
    bus = dbus.SystemBus()

    manager = dbus.Interface(
        bus.get_object("org.bluez", "/"),
        "org.freedesktop.DBus.ObjectManager"
    )

    objects = manager.GetManagedObjects()

    devices = []

    for dev_path, interfaces in objects.items():
        if "org.bluez.Device1" in interfaces.keys():
            properties = objects[dev_path]["org.bluez.Device1"]

            if properties["Connected"] == 1:
                devices.append((properties["Address"], properties["Name"]))

    return devices


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    device_separator = '|'
    format = '{name}'
    format_no_conn = 'OFF'
    format_no_conn_prefix = 'BT: '
    format_prefix = 'BT: '

    def bluetooth(self):
        color = self.py3.COLOR_BAD

        devices = get_connected_devices()

        if devices:
            data = []
            for mac, name in devices:
                fmt_str = self.py3.safe_format(
                    self.format,
                    {'name': name, 'mac': mac}
                )
                data.append(fmt_str)

            output = self.py3.safe_format(
                '{format_prefix}{data}',
                {'format_prefix': self.format_prefix,
                 'data': self.device_separator.join(data)}
            )

            color = self.py3.COLOR_GOOD
        else:
            output = self.py3.safe_format(
                '{format_prefix}{format}',
                dict(format_prefix=self.format_no_conn_prefix,
                     format=self.format_no_conn)
            )

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': output,
            'color': color,
        }

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
