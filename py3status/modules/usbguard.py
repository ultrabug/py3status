# -*- coding: utf-8 -*-
"""
USBGuard i3 companion to replace default 'usbguard-applet-qt'.
Show an indicator when a new usb device is plugged,
we can allow or reject a device.

Configuration parameters:
    button_allow: Button to allow the device. (default 1)
    button_block: Button to block the device (default 3)
    button_reject: Button to reject the device. (default None)
    format: Display format for the module. (default '[USBGuard: [{name}]]')

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
        device = self.parent.device
        device_perms = event[4][3]
        device_state = event[4][1]

        # if inserted
        if device_state == 1:  # 1 inserted, 3 removed
            if 'block id' in device_perms:
                device['usbguard_id'] = event[4][0]
                for new_key in device:
                    old_key = new_key.replace('_', '-')
                    if old_key in event[4][4]:
                        if event[4][4][old_key]:
                            device[new_key] = event[4][4][old_key]
                        else:
                            device[new_key] = None
        else:
            # 'reset' device
            for new_key in device:
                old_key = new_key.replace('_', '-')
                device[new_key] = None
        self.parent.device = device
        self.parent.py3.update()

    # on policy change signal
    def _on_devices_policy_changed(self, *event):
        device = self.parent.device
        # TODO: send notification with action
        device_perms = event[4][3]
        actions = ['allow id', 'reject id']
        for action in actions:
            if action in device_perms:
                for new_key in device:
                    device[new_key] = None
                self.parent.device = device
                self.parent.py3.update()
                break

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
    format = u'[USBGuard: [{name}]]'

    def _init_dbus(self):
        self.dbus_interface = 'org.usbguard'
        self.dbus_devices = '/org/usbguard/Devices'
        self.dbus = SystemBus()
        self.error = None
        try:
            self.proxy = self.dbus.get(self.dbus_interface)
        except:
            self.error = Exception(STRING_USBGUARD_DBUS)

    def post_config_hook(self):
        placeholders = [
            'id', 'name', 'via_port', 'hash', 'parent_hash', 'serial',
            'with_interface'
        ]
        self.device = {}
        for placeholder in placeholders:
            if self.py3.format_contains(self.format, placeholder):
                self.device[placeholder] = None
        self.device['usbguard_id'] = None

        self._init_dbus()

        self.permanant = False
        self.killed = threading.Event()
        UsbguardListener(self).start()

    def _usbguard_cmd(self, action):
        targets = {'allow': 0, 'block': 1, 'reject': 2}
        return self.proxy.applyDevicePolicy(self.device['usbguard_id'],
                                            targets[action], self.permanant)

    def kill(self):
        self.killed.set()

    def on_click(self, event):
        button = event['button']
        if button == self.button_allow:
            self._usbguard_cmd('allow')
        elif button == self.button_reject:
            self._usbguard_cmd('reject')
        elif button == self.button_block:
            for key in self.device:
                self.device[key] = None
        sleep(0.1)
        self.py3.update()

    def usbguard(self):
        if self.error:
            self.py3.error(str(self.error), self.py3.CACHE_FOREVER)

        return {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(self.format, self.device),
            'urgent': True
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
