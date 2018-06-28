# -*- coding: utf-8 -*-
"""
USBGuard i3 companion to replace default 'usbguard-applet-qt'.
Show an indicator when a new usb device is plugged,
we can allow or reject a device.

Configuration parameters:
    button_allow: Button to allow the device. (default 1)
    button_block: Button to block the device (default 3)
    button_reject: Button to reject the device. (default None)
    format: Display format for the module. (default '[USBGuard: {name}]')
    format_separator: format separator for usb devices. (default ' | ')

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
    usbguard: usb device authorization policy framework

@author Cyril Levis (@cyrinux)
@license BSD

SAMPLE OUTPUT
{'full_text': 'USBGuard: Mass Storage', 'urgent': True}
"""

import threading
from time import sleep

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
        else:
            if self.parent.data[usbguard_id]:
                del self.parent.data[usbguard_id]

        self.parent.new_data = self.parent._manipulate_devices(
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
                if self.parent.data[usbguard_id]:
                    del self.parent.data[usbguard_id]
                    break

        self.parent.new_data = self.parent._manipulate_devices(
            self.parent.data)
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
    format = u'[USBGuard: {name}]'
    format_separator = u' | '

    def _init_dbus(self):
        self.dbus_interface = 'org.usbguard'
        self.dbus_devices = '/org/usbguard/Devices'
        self.dbus = SystemBus()
        self.error = None
        try:
            self.proxy = self.dbus.get(self.dbus_interface)
        except:
            self.error = Exception(STRING_USBGUARD_DBUS)

    def _init_placeholders(self):
        available_placeholders = [
            'id', 'name', 'via_port', 'hash', 'parent_hash', 'serial',
            'with_interface'
        ]

        placeholders = {}

        for placeholder in available_placeholders:
            if self.py3.format_contains(self.format, placeholder):
                placeholders[placeholder] = None

        placeholders['usbguard_id'] = None
        return placeholders

    def post_config_hook(self):
        self._init_dbus()
        self.data = {}
        self.new_data = []

        self.placeholders = self._init_placeholders()

        self.permanant_rule = False
        self.killed = threading.Event()
        UsbguardListener(self).start()

    def _usbguard_cmd(self, action, usbguard_id):
        if action and int(usbguard_id):
            targets = {'allow': 0, 'block': 1, 'reject': 2}
            if action == 'block':
                if self.data[usbguard_id]:
                    del self.data[usbguard_id]
                    self.new_data = self._manipulate_devices(self.data)
                    self.py3.update()

            return self.proxy.applyDevicePolicy(
                usbguard_id, targets[action], self.permanant_rule
            )

    def kill(self):
        self.killed.set()

    def on_click(self, event):
        self.py3.log(event)
        button = event['button']
        usbguard_id = event['index']
        if button == self.button_allow:
            self._usbguard_cmd('allow', usbguard_id)
        elif button == self.button_reject:
            self._usbguard_cmd('reject', usbguard_id)
        elif button == self.button_block:
            self._usbguard_cmd('block', usbguard_id)
        sleep(0.1)
        self.py3.update()

    def _manipulate_devices(self, data):
        composite = []
        for device in data:
            device_formatted = self.py3.safe_format(self.format, data[device])
            self.py3.composite_update(device_formatted,
                                      {'index': data[device]['index']})
            composite.append(device_formatted)

        format_separator = self.py3.safe_format(self.format_separator)

        return self.py3.composite_join(format_separator, composite)

    def usbguard(self):
        if self.error:
            self.py3.error(str(self.error), self.py3.CACHE_FOREVER)

        return {
            'cached_until': self.py3.CACHE_FOREVER,
            'composite': self.new_data,
            'urgent': True
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
