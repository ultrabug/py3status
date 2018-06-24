# -*- coding: utf-8 -*-
# UsbGuard module
from gi.repository import GLib
from pydbus import SystemBus
from threading import Thread


class Py3status:
    format = u'usb: {device_name} / id: {device_id}'
    cache_timeout = 60
    data = {'device_name': '', 'device_id': ''}

    def post_config_hook(self):
        self.usbguard_thread = Thread()
        self.bus = SystemBus()
        self.proxy = self.bus.get('org.usbguard')
        self.proxy_devices = self.proxy[".Devices"]

    def _get_last_device(self):
        self.loop = GLib.MainLoop()
        devices_filter = '/org/usbguard/Devices'

        def cb_devices_presence_changed(*args):
            device = args[4]
            data = {'device_name': '', 'device_id': ''}
            device_name = device[4]['name']
            device_id = device[0]
            if not data['device_name'] or data['device_name'] != device_name:
                data['device_name'] = device_name
                data['device_id'] = device_id
            self.data = data

        self.bus.subscribe(
            object=devices_filter,
            signal='DevicePresenceChanged',
            signal_fired=cb_devices_presence_changed)

        self.loop.run()

    def usbguard(self):
        self.usbguard_thread = Thread(target=self._get_last_device)
        self.usbguard_thread.daemon = True
        self.usbguard_thread.start()
        self.py3.update()
        return {
            'cached_until':
            self.py3.time_in(self.cache_timeout),
            'full_text':
            self.py3.safe_format(
                self.format, {
                    'device_id': self.data['device_id'],
                    'device_name': self.data['device_name']
                })
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
