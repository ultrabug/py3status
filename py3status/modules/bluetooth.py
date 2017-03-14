# -*- coding: utf-8 -*-
"""
Display bluetooth status.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    device_separator: show separator only if more than one (default '|')
    format: display format for this module (default 'BT[: {format_device}]')
    format_device: display format for bluetooth devices (default '{name}')

Format placeholders:
    {format_device} format for bluetooth devices

format_device placeholders:
    {mac} bluetooth device address
    {name} bluetooth device name

Color options:
    color_bad: No connection
    color_good: Active connection

@author jmdana <https://github.com/jmdana>
@license GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>
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
    format = 'BT[: {format_device}]'
    format_device = '{name}'

    class Meta:
        def deprecate_function(config):
            out = {}
            if 'format_prefix' in config:
                out['format'] = u'{}{{format_device}}'.format(config['format_prefix'])
            return out
        deprecated = {
            'function': [
                {'function': deprecate_function},
            ],
        }

    def bluetooth(self):
        devices = get_connected_devices()

        if devices:
            data = []
            for mac, name in devices:
                data.append(self.py3.safe_format(self.format_device, {'name': name, 'mac': mac}))
            full_text = self.py3.composite_join(self.device_separator, data)
            color = self.py3.COLOR_GOOD
        else:
            full_text = None
            color = self.py3.COLOR_BAD

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'format_device': full_text}),
            'color': color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
