# -*- coding: utf-8 -*-
# """
#
# need usbguard dbus service running
# sudo systemctl enable --now usbguard-dbus.service
#
# middle clic reject
# left clic allow
# @author Cyril Levis (@cyrinux)
# """

from gi.repository import GLib
from pydbus import SystemBus
from threading import Thread
from time import sleep

USBGUARD_CMD = """usbguard {action}-device {device_id}"""


class Py3status:
    format = u'usbguard: {device_name}'
    button_allow = 1
    button_block = None
    button_reject = 3
    allow_urgent = False

    def post_config_hook(self):
        self.usbguard_thread = Thread()
        self.bus = SystemBus()
        self.proxy = self.bus.get('org.usbguard')
        self.proxy_devices = self.proxy[".Devices"]
        self.device = {
            'device_name': None,
            'device_id': None,
            'device_hash': None
        }

    def _usbguard_cmd(self, action):
        return USBGUARD_CMD.format(
            action=action, device_id=self.device['device_id'])

    def _loop_devices(self):
        self.loop = GLib.MainLoop()
        devices_filter = '/org/usbguard/Devices'

        # on device change signal
        def cb_devices_presence_changed(*args):
            device = self.device
            device_args = args[4]
            device_id = device_args[0]
            device_hash = device_args[4]['hash']
            device_name = device_args[4]['name']
            device_perms = device_args[3]
            device_status = device_args[1]

            # if device inserted (1), removed (3)
            if device_status == 1:
                # if it is blocked device
                if 'block id' in str(device_perms) and device_name:
                    # TODO: add device to an array
                    device['device_name'] = device_name
                    device['device_id'] = device_id
                    device['device_hash'] = device_hash
                    self.py3.update()
            # TODO: remove device from array if removed
            else:
                device['device_name'] = None
                device['device_id'] = None
                device['device_hash'] = None
                self.py3.update()
            self.device = device

        self.bus.subscribe(
            object=devices_filter,
            signal='DevicePresenceChanged',
            signal_fired=cb_devices_presence_changed)

        # on policy change signal
        def cb_devices_policy_changed(*args):
            device = self.device
            device_args = args[4]
            device_perms = device_args[3]
            if 'reject id' in device_perms:
                device['device_name'] = None
                device['device_id'] = None
                device['device_hash'] = None
                self.device = device
                self.py3.update()
            elif 'allow id' in device_perms:
                device['device_name'] = None
                device['device_id'] = None
                device['device_hash'] = None
                self.device = device
                self.py3.update()

        self.bus.subscribe(
            object=devices_filter,
            signal='DevicePolicyChanged',
            signal_fired=cb_devices_policy_changed)

        self.loop.run()

    def usbguard(self):
        """
        """
        self.usbguard_thread = Thread(target=self._loop_devices)
        self.usbguard_thread.daemon = True
        self.usbguard_thread.start()

        if self.allow_urgent:
            urgent = True

        return {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(self.format, self.device),
            'urgent': urgent
        }

    def on_click(self, event):
        """
        """
        button = event['button']
        if self.button_allow and button == self.button_allow:
            action = 'allow'
            self.py3.command_run(self._usbguard_cmd(action))
        elif self.button_reject and button == self.button_reject:
            action = 'reject'
            self.py3.command_run(self._usbguard_cmd(action))
        elif self.button_block and button == self.button_block:
            action = 'block'
            self.py3.command_run(self._usbguard_cmd(action))
            sleep(0.1)
        self.py3.update()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
