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
    {name} the device name of last device plugged.
    {usbguard_id} the usbguard device id of last device plugged.
    {device_hash} the usbguard device unique hash of last device plugged.

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

    def _setup_dbus(self):
        self.dbus = SystemBus()
        try:
            self.parent.error = None
            self.proxy = self.dbus.get(self.parent.dbus_interface)
        except:
            self.parent.error = Exception(STRING_USBGUARD_DBUS)

    # on device change signal
    def _on_devices_presence_changed(self, *event):
        device = self.parent.device
        device_perms = event[4][3]
        device_state = event[4][1]

        # 'reset' device
        for key in device:
            device[key] = None

        # if inserted
        if device_state == 1:  # 1 inserted, 3 removed
            if 'block id' in device_perms:
                device['usbguard_id'] = event[4][0]
                for key in device:
                    if key in event[4][4]:
                        if event[4][4][key]:
                            device[key] = event[4][4][key]
                        else:
                            device[key] = None
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
                for key in device:
                    device[key] = None
                self.parent.device = device
                self.parent.py3.update()
                break

    def run(self):
        while not self.parent.killed.is_set():
            self._setup_dbus()
            self.dbus.subscribe(
                object=self.parent.dbus_devices,
                signal='DevicePresenceChanged',
                signal_fired=self._on_devices_presence_changed)

            self.dbus.subscribe(
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

    def post_config_hook(self):
        placeholders = [
            'id', 'name', 'via-port', 'hash', 'parent-hash', 'serial',
            'with-interface'
        ]
        self.device = {}
        for placeholder in placeholders:
            if self.py3.format_contains(self.format, placeholder):
                self.device[placeholder] = None
        self.device['usbguard_id'] = None
        self.dbus_interface = 'org.usbguard'
        self.dbus_devices = '/org/usbguard/Devices'
        self.error = None
        self.dbus = SystemBus()
        try:
            self.proxy = self.dbus.get(self.dbus_interface)
        except:
            self.parent.error = Exception(STRING_USBGUARD_DBUS)

        self.targets = {'allow': 0, 'block': 1, 'reject': 2}
        self.permanant = False
        self.killed = threading.Event()
        UsbguardListener(self).start()

    def _usbguard_cmd(self, action):
        return self.proxy.applyDevicePolicy(
            self.device['usbguard_id'], self.targets[action], self.permanant)

    def kill(self):
        self.killed.set()

    def on_click(self, event):
        button = event['button']
        action = None
        if button == self.button_allow:
            action = 'allow'
        elif button == self.button_reject:
            action = 'reject'
        elif button == self.button_block:
            # 'reset' device
            for key in self.device:
                self.device[key] = None
        if action:
            self._usbguard_cmd(action)
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
