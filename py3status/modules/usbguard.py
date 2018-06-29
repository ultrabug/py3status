# -*- coding: utf-8 -*-
"""
USBGuard i3 companion to replace default 'usbguard-applet-qt'.
Show an indicator when a new usb device is plugged,
we can allow or reject a device.

Configuration parameters:
    button_allow: Button to allow the device. (default 1)
    button_block: Button to block the device (default 3)
    button_reject: Button to reject the device. (default None)
    format: Display format for the module. (default '[{format_device}]')
    format_device: format separator for usb devices. (default '{name}')
    format_device_separator: format separator for usb devices. (default ' | ')

Format placeholders:
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


@author Cyril Levis (@cyrinux)
@license BSD

SAMPLE OUTPUT
{'full_text': 'Mass Storage', 'urgent': True}
"""

import threading

from gi.repository import GLib
from pydbus import SystemBus

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
                device = dict(usbguard_id=usbguard_id, index=usbguard_id)
                for new_key in self.parent.placeholders:
                    old_key = new_key.replace('_', '-')
                    if old_key in event[4][4]:
                        if event[4][4][old_key]:
                            device[new_key] = event[4][4][old_key]
                        else:
                            device[new_key] = None
                self.parent.data[usbguard_id] = device
                self.parent.new_data[
                    'format_device'] = self.parent._manipulate_devices(
                        self.parent.data)
        else:
            if usbguard_id in self.parent.data:
                del self.parent.data[usbguard_id]
                self.parent.new_data[
                    'format_device'] = self.parent._manipulate_devices(
                        self.parent.data)
        self.parent.py3.update()

    # on policy change signal
    def _on_devices_policy_changed(self, *event):
        # TODO: send notification with action
        usbguard_id = event[4][0]
        device_perms = event[4][3]
        actions = ['allow id', 'reject id']
        for action in actions:
            if action in device_perms:
                if usbguard_id in self.parent.data:
                    del self.parent.data[usbguard_id]
                    self.parent.new_data[
                        'format_device'] = self.parent._manipulate_devices(
                            self.parent.data)
                    break
        self.parent.py3.update()

    def run(self):
        while not self.parent.killed.is_set():
            self.parent._init_dbus()
            self.parent.dbus.subscribe(
                object=self.parent.dbus_devices,
                signal='DevicePresenceChanged',
                signal_fired=self._on_devices_presence_changed)

            self.parent.dbus.subscribe(
                object=self.parent.dbus_devices,
                signal='DevicePolicyChanged',
                signal_fired=self._on_devices_policy_changed)

            self.loop = GLib.MainLoop()
            self.loop.run()


class Py3status:
    """
    """
    button_allow = 1
    button_block = 3
    button_reject = None
    format = u'[{format_device}]'
    format_device = u'{name}'
    format_device_separator = u' | '

    def _init_dbus(self):
        self.dbus_interface = 'org.usbguard'
        self.dbus_devices = '/org/usbguard/Devices'
        self.dbus = SystemBus()
        self.error = None
        try:
            self.proxy = self.dbus.get(self.dbus_interface)
        except:
            self.error = Exception(STRING_USBGUARD_DBUS)

    def _toggle_permanant(self):
        self.is_permanant = not self.is_permanant

    def post_config_hook(self):
        self._init_dbus()
        self.data = {}
        self.new_data = {}
        self.is_permanant = False

        # init placeholders
        available_placeholders = [
            'id', 'name', 'via_port', 'hash', 'parent_hash', 'serial',
            'with_interface', 'format_device'
        ]

        self.placeholders = {}

        for placeholder in available_placeholders:
            if self.py3.format_contains(self.format_device, placeholder):
                self.placeholders[placeholder] = None

        self.placeholders['usbguard_id'] = None

        self.killed = threading.Event()
        UsbguardListener(self).start()

    def _set_policy(self, action, usbguard_id):
        if action and int(usbguard_id):
            targets = {'allow': 0, 'block': 1, 'reject': 2}
            if action == 'block':
                if self.data[usbguard_id]:
                    del self.data[usbguard_id]
                    self.new_data['format_devices'] = self._manipulate_devices(
                        self.data)
                    self.py3.update()

            self.proxy.applyDevicePolicy(usbguard_id, targets[action],
                                         self.is_permanant)

    def kill(self):
        self.killed.set()

    def on_click(self, event):
        button = event['button']
        usbguard_id = event['index']
        if button == self.button_allow:
            self._set_policy('allow', usbguard_id)
        elif button == self.button_reject:
            self._set_policy('reject', usbguard_id)
        elif button == self.button_block:
            self._set_policy('block', usbguard_id)

    def _manipulate_devices(self, data):
        format_device = []
        format_device_separator = self.py3.safe_format(
            self.format_device_separator)
        self.py3.composite_update(format_device_separator, {'index': 'sep'})

        for device in data:
            device_formatted = self.py3.safe_format(self.format_device,
                                                    data[device])
            self.py3.composite_update(device_formatted,
                                      {'index': data[device]['index']})
            format_device.append(device_formatted)

            format_device = self.py3.composite_join(format_device_separator,
                                                    format_device)

        return format_device

    def usbguard(self):
        if self.error:
            self.py3.error(str(self.error), self.py3.CACHE_FOREVER)

        response = {'cached_until': self.py3.CACHE_FOREVER, 'urgent': True}

        if len(self.new_data):
            composite = self.py3.safe_format(self.format, self.new_data)
            response['composite'] = composite
        else:
            response['full_text'] = self.py3.safe_format(
                self.format, {'format_device': ''})

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
