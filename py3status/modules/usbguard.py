# -*- coding: utf-8 -*-
"""
Usbguard i3 companion to replace default 'usbguard-applet-qt'.
Show an indicator when a new usb device is plugged,
we can allow or reject a device.

Configuration parameters:
    allow_urgent: Allow urgent (default False)
    button_allow: Button to allow the device. (default 1)
    button_block: Button to block the device (default None)
    button_reject: Button to reject the device. (default 3)
    format: Display format for the module. (default '[UsbGuard: [{device_name}]]')

Format placeholders:
    {device_name} the device name of last device plugged.
    {device_id} the usbguard device id of last device plugged.
    {device_hash} the usbguard device unique hash of last device plugged.

Requires:
    https://usbguard.github.io:
    "The USBGuard software framework helps to protect your
    computer against rogue USB devices..."

@author Cyril Levis (@cyrinux)
@license BSD

SAMPLE OUTPUT
{'full_text': 'Usbguard: Mass Storage', 'urgent': True}
"""

import threading
from time import sleep
from gi.repository import GLib
from pydbus import SystemBus

DBUS_INTERFACE = 'org.usbguard'
DBUS_DEVICE_FILTER = '/org/usbguard/Devices'


class UsbguardListener(threading.Thread):
    def __init__(self, parent):
        super(UsbguardListener, self).__init__()
        self.parent = parent

    def _setup_dbus(self):
        self.dbus = SystemBus()
        self.dbus_devices_filter = DBUS_DEVICE_FILTER
        try:
            self.parent.error = None
            self.proxy = self.dbus.get(DBUS_INTERFACE)
            self.proxy_devices = self.proxy[".Devices"]
        except:
            self.parent.error = Exception("usbguard-dbus service not running")

    # on device change signal
    def _cb_devices_presence_changed(self, *args):
        device = self.parent.device
        device_args = args[4]
        device_hash = device_args[4]['hash']
        device_id = device_args[0]
        device_name = device_args[4]['name']
        device_perms = device_args[3]
        device_status = device_args[1]
        device['device_name'] = None
        device['device_id'] = None
        device['device_hash'] = None

        # if device inserted (1), removed (3)
        if device_status == 1:
            device['device_hash'] = device_hash
            device['device_id'] = device_id
            device['device_name'] = device_name
            if 'block id' in device_perms:
                self.parent.device = device
        self.parent.py3.update()

    # on policy change signal
    def _cb_devices_policy_changed(self, *args):
        device = self.parent.device
        device_args = args[4]
        device_perms = device_args[3]
        actions = ['allow', 'reject']
        for x in actions:
            if x in device_perms:
                device['device_name'] = None
                device['device_id'] = None
                device['device_hash'] = None
                self.parent.device = device
                self.parent.py3.update()
                break

    def run(self):
        while not self.parent.killed.is_set():
            self._setup_dbus()
            self.dbus.subscribe(
                object=self.dbus_devices_filter,
                signal='DevicePresenceChanged',
                signal_fired=self._cb_devices_presence_changed)

            self.dbus.subscribe(
                object=self.dbus_devices_filter,
                signal='DevicePolicyChanged',
                signal_fired=self._cb_devices_policy_changed)

            self.loop = GLib.MainLoop()
            self.loop.run()


class Py3status:
    # available configuration options
    allow_urgent = False
    button_allow = 1
    button_block = None
    button_reject = 3
    format = u'[UsbGuard: [{device_name}]]'

    def post_config_hook(self):
        self.device = {
            'device_name': None,
            'device_id': None,
            'device_hash': None
        }
        self.error = None
        self.dbus = SystemBus()
        try:
            self.proxy = self.dbus.get(DBUS_INTERFACE)
        except:
            self.parent.error = Exception("usbguard-dbus service not running")

        self.targets = {'allow': 0, 'block': 1, 'reject': 2}
        self.killed = threading.Event()
        UsbguardListener(self).start()

    def _usbguard_dbus_cmd(self, action):
        return self.proxy.applyDevicePolicy(self.device['device_id'],
                                            self.targets[action], 0)

    def usbguard(self):
        """
        """
        if self.error:
            self.py3.error(str(self.error), self.py3.CACHE_FOREVER)

        response = {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(self.format, self.device)
        }
        if self.allow_urgent:
            response['urgent'] = True
        return response

    def on_click(self, event):
        """
        """
        button = event['button']
        action = None
        if self.button_allow and button == self.button_allow:
            action = 'allow'
        elif self.button_reject and button == self.button_reject:
            action = 'reject'
        elif self.button_block and button == self.button_block:
            action = 'block'

        if action:
            self._usbguard_dbus_cmd(action)
            sleep(0.1)
            self.py3.update()

    def kill(self):
        self.killed.set()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
