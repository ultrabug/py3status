#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
USBGuard i3 companion to replace default 'usbguard-applet-qt'.
Show an indicator when a new usb device is plugged,
we can allow or reject a device.

Configuration parameters:
    button_allow: Button to allow the device. (default 1)
    button_block: Button to block the device (default 3)
    button_reject: Button to reject the device. (default None)
    format: Display format for the module. (default '{format_all_devices}')
    format_all_devices: format separator for usb devices.
        (default '\?color=rule {name} is {rule}')
    format_device_separator: format separator for usb devices. (default '\?color=separator  \| ')
    format_notification: format for notification on action (default '{name} is {action}')
    thresholds: specify color thresholds to use
        *(default {
            'action': [
                ('block', "bad"), ('reject', "degraded"), ('allow', "good")],
            'rule': [
                ('block', "bad"), ('reject', "degraded"), ('allow', "good")]})*

Format placeholders:
    {format_all_devices} format device list

format_all_devices:
    {hash} the usbguard device unique hash of last device plugged.
    {name} the device name of last device plugged.
    {parent_hash} the usbguard port hash where device is plugged.
    {serial} ???
    {usbguard_id} the usbguard device id of last device plugged.
    {via_port} the usb port where device is plugged.
    {with_interface} ???

format_notification:
    {action} action taken for the device
    {hash} the usbguard device unique hash of last device plugged.
    {name} the device name of last device plugged.
    {parent_hash} the usbguard port hash where device is plugged.
    {serial} ???
    {usbguard_id} the usbguard device id of last device plugged.
    {via_port} the usb port where device is plugged.
    {with_interface} ???

Requires:
    pydbus: pythonic dbus library
    python-gobject: pythonic binding for gobject
    usbguard: usb device authorization policy framework, WITHOUT usbguard-applet-qt running

```
Ex:
Show only block devices:
format_all_devices = '\?if=rule=block   {name} is {rule}'
```

@author Cyril Levis (@cyrinux)

@license BSD

SAMPLE OUTPUT
{'full_text': 'Mass Storage', 'urgent': True}
"""

import threading

from gi.repository import GLib
from pydbus import SystemBus
# import re

STRING_USBGUARD_DBUS = 'usbguard-dbus service not running'


class UsbguardListener(threading.Thread):
    """
    """

    def __init__(self, parent):
        super(UsbguardListener, self).__init__()
        self.parent = parent

    # on device change signal
    def _on_devices_presence_changed(self, *event):
        device_perms = event[4][3]
        device_state = event[4][1]
        usbguard_id = event[4][0]

        # if inserted
        if device_state == 1:  # 1 inserted, 3 removed
            if 'block id' in device_perms:
                device = dict(usbguard_id=usbguard_id)
                for new_key in self.parent.placeholders:
                    old_key = new_key.replace('_', '-')
                    if old_key in event[4][4]:
                        if event[4][4][old_key]:
                            device[new_key] = event[4][4][old_key]
                        else:
                            device[new_key] = None
                self.parent.data[usbguard_id] = device
        else:
            if usbguard_id in self.parent.data:
                del self.parent.data[usbguard_id]

        self.parent.all_devices = self.parent._get_all_devices()
        self.parent.py3.update()

    # on policy change signal
    def _on_devices_policy_changed(self, *event):
        usbguard_id = event[4][0]
        device_perms = event[4][3]
        actions = ['allow id', 'reject id']
        for action in actions:
            if action in device_perms:
                if usbguard_id in self.parent.data:
                    del self.parent.data[usbguard_id]
                    break

        self.parent.all_devices = self.parent._get_all_devices()
        self.parent.py3.update()

    def run(self):
        while not self.parent.killed.is_set():
            self.parent._init_dbus()
            self.parent.dbus.subscribe(
                object=self.parent.dbus_devices,
                signal='DevicePresenceChanged',
                signal_fired=self._on_devices_presence_changed,
            )

            self.parent.dbus.subscribe(
                object=self.parent.dbus_devices,
                signal='DevicePolicyChanged',
                signal_fired=self._on_devices_policy_changed,
            )

            self.loop = GLib.MainLoop()
            self.loop.run()


class Py3status:
    """
    """

    button_allow = 1
    button_block = 3
    button_reject = None
    format = u'{format_all_devices}'
    format_all_devices = u'\?color=rule {name} is {rule}'
    format_device_separator = u'\?color=separator  \| '
    format_notification = u'{name} is {action}'
    thresholds = {
        'action': [('block', "bad"), ('reject', "degraded"), ('allow', "good")],
        'rule': [('block', "bad"), ('reject', "degraded"), ('allow', "good")],
    }

    def _init_dbus(self):
        self.dbus_interface = 'org.usbguard'
        self.dbus_devices = '/org/usbguard/Devices'
        self.dbus = SystemBus()
        self.error = None
        try:
            self.proxy = self.dbus.get(self.dbus_interface, self.dbus_devices)
        except:  # noqa e722
            self.error = Exception(STRING_USBGUARD_DBUS)

    def _get_all_devices(self):
        devices_array = []
        response = {}
        # TODO: filter, match, allow, block
        devices = self.proxy.listDevices('match')
        keys = [
            'serial',
            'rule',
            'id',
            'name',
            'hash',
            'parent_hash',
            'via_port',
            'with_interface',
        ]
        # _regex_serial = re.compile(r'\S*serial \"(\S+)\"\S*')
        # _regex_rule = re.compile(r'^(\S+)')
        # _regex_id = re.compile(r'id (\S+)')
        # _regex_name = re.compile(r'name \"(.*)\" hash')
        # _regex_hash = re.compile(r'hash \"(.*)\" parent-hash')
        # _regex_parent_hash = re.compile(r'parent-hash \"(.*)\" via-port')
        # _regex_via_port = re.compile(r'via-port \"(.*)\" with-interface')
        # _regex_with_interface = re.compile(r'with-interface \{ (.*) \}$')

        for usbguard_id, device in devices:
            params = {}
            params['usbguard_id'] = usbguard_id
            for key in keys:
                value = None
                regex = eval('_regex_' + key)
                value = regex.findall(device)
                if value:
                    value = value[0]
                    value = value.encode('latin-1').decode('unicode_escape')
                    value = value.encode('latin-1').decode('utf-8')
                else:
                    value = ''
                params[key] = value
            devices_array.append(params)

        for index, device in sorted(enumerate(devices_array), reverse=False):
            response[index + 1] = device

        # self.py3.log('# response')
        # self.py3.log(response)

        return response

    def _toggle_permanant(self):
        self.is_permanent = not self.is_permanent

    def post_config_hook(self):
        self._init_dbus()
        self.all_devices = {}
        self.data = {}
        self.usbguard_data = {}
        self.is_permanent = False

        # init placeholders
        available_placeholders = [
            'id',
            'name',
            'via_port',
            'hash',
            'parent_hash',
            'serial',
            'with_interface',
            'format_all_devices',
        ]
        self.placeholders = {}
        placeholders = self.py3.get_placeholders_list(
            self.format_notification + self.format_all_devices
        )
        for placeholder in available_placeholders:
            if placeholder in placeholders:
                self.placeholders[placeholder] = None
        self.placeholders['usbguard_id'] = None

        self.killed = threading.Event()
        UsbguardListener(self).start()

    def _set_policy(self, action, index):
        if action and index and index != 'sep':

            targets = {'allow': 0, 'block': 1, 'reject': 2}

            self.py3.log('# data')
            self.py3.log(self.data)
            self.py3.log('# index')
            self.py3.log(index)
            self.py3.log('# action')
            self.py3.log(action)
            self.py3.log('# usbguard data')
            self.py3.log(self.usbguard_data)
            self.py3.log('# all devices')
            self.py3.log(self.all_devices)

            # notifications
            if self.format_notification:
                format_notification = self.data[index]
                format_notification['action'] = action
                format_notification = self.py3.safe_format(
                    self.format_notification, format_notification
                )
                notification = self.py3.get_composite_string(format_notification)
                self.py3.notify_user(
                    notification,
                    title='USBGuard',
                    icon='/usr/share/icons/hicolor/scalable/apps/usbguard-icon.svg',
                )

            # apply policy
            if 'usbguard_id' in self.data and index != 'sep':
                self.proxy.applyDevicePolicy(
                    self.data['usbguard_id'], targets[action], self.is_permanent
                )

    def _manipulate_all_devices(self, data):
        format_all_devices = []
        format_device_separator = self.py3.safe_format(self.format_device_separator)
        self.py3.composite_update(format_device_separator, {'index': 'sep'})

        for device in data:
            for x in self.thresholds:
                if x in data[device]:
                    self.py3.threshold_get_color(data[device][x], x)

            device_formatted = self.py3.safe_format(
                self.format_all_devices, data[device]
            )

            # add usbguard_id
            self.py3.composite_update(
                device_formatted, {'usbguard_id': data[device]['usbguard_id']}
            )

            format_all_devices.append(device_formatted)

        for index, device in sorted(enumerate(format_all_devices), reverse=False):
            format_all_devices[index] = device

        format_all_devices = self.py3.composite_join(
            format_device_separator, format_all_devices
        )

        return format_all_devices

    def usbguard(self):
        if self.error:
            self.py3.error(str(self.error), self.py3.CACHE_FOREVER)

        self.all_devices = self._get_all_devices()
        self.usbguard_data['format_all_devices'] = self._manipulate_all_devices(
            self.all_devices
        )

        response = {'cached_until': self.py3.CACHE_FOREVER, 'urgent': True}

        if len(self.usbguard_data) > 0:
            composite = self.py3.safe_format(self.format, self.usbguard_data)
            response['composite'] = composite
        else:
            response['full_text'] = self.py3.safe_format(
                self.format, {'format_all_devices': ''}
            )

        return response

    def kill(self):
        self.killed.set()

    def on_click(self, event):
        button = event['button']
        index = event['index']

        self.py3.log('# click event')
        self.py3.log(event)

        if button == self.button_allow:
            self._set_policy('allow', index)
        elif button == self.button_reject:
            self._set_policy('reject', index)
        elif button == self.button_block:
            self._set_policy('block', index)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
