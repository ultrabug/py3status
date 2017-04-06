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

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'BT: Microsoft Bluetooth Notebook Mouse 5000'}

off
{'color': '#FF0000', 'full_text': u'BT'}
"""

import dbus

DEFAULT_FORMAT = 'BT[: {format_device}]'
STRING_NOT_STARTED = "service isn't running"


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
    format = DEFAULT_FORMAT
    format_device = '{name}'

    def post_config_hook(self):
        # Do deprecation stuff here.  Because of the complexity we can't use
        # the usual deprecation methods
        # THIS IS A SPECIAL CASE DO NOT USE AS EXAMPLE CODE.
        format_prefix = getattr(self, 'format_prefix', None)
        format_no_conn = getattr(self, 'format_no_conn', None)
        format_no_conn_prefix = getattr(self, 'format_no_conn_prefix', None)

        placeholders = set(self.py3.get_placeholders_list(self.format))
        if set(['name', 'mac']) & placeholders:
            # this is an old format so should be format_device
            self.format_device = self.format
            self.format = DEFAULT_FORMAT
            msg = 'DEPRECATION WARNING: your format is using invalid '
            msg += 'placeholders you should update your configuration.'
            self.py3.log(msg)

        if self.format != DEFAULT_FORMAT:
            # The user has set a format using the new style format so we are
            # done here.
            return

        if format_prefix or format_no_conn_prefix or format_no_conn:
            # create a format that will give the expected output
            self.format = u'[\?if=format_device {}{{format_device}}|{}{}]'.format(
                format_prefix or 'BT: ',
                format_no_conn_prefix or 'BT: ',
                format_no_conn or 'OFF'
            )
            msg = 'DEPRECATION WARNING: you are using old style configuration '
            msg += 'parameters you should update to use the new format.'
            self.py3.log(msg)

    def bluetooth(self):
        try:
            devices = get_connected_devices()
        except dbus.DBusException:
            self.py3.error(STRING_NOT_STARTED)

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
