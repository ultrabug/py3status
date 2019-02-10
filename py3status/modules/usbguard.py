# -*- coding: utf-8 -*-
"""
Allow or Reject newly plugged USB devices using USBGuard.

Configuration parameters:
    format: display format for this module
        (default '{format_device}')
    format_button_allow: display format for allow button filter
        (default '\[Allow\]')
    format_button_reject: display format for reject button filter
        (default '\[Reject\]')
    format_device: display format for USB devices
        (default '{format_button_reject} [{name}|{usb_id}] {format_button_allow}')
    format_device_separator: show separator if more than one (default ' ')

Format placeholders:
    {device}                  number of USB devices
    {format_device}           format for USB devices

format_device:
    {format_button_allow}     button to allow the device
    {format_button_reject}    button to reject the device
    {id}                      eg 1, 2, 5, 6, 7, 22, 23, 33
    {policy}                  eg allow, block, reject
    {usb_id}                  eg 054c:0268
    {name}                    eg Poker II, PLAYSTATION(R)3 Controller
    {serial}                  eg 0000:00:00.0
    {port}                    eg usb1, usb2, usb3, 1-1, 4-1.2.1
    {interface}               eg 00:00:00:00 00:00:00 00:00:00
    {hash}                    eg ihYz60+8pxZBi/cm+Q/4Ibrsyyzq/iZ9xtMDAh53sng
    {parent_hash}             eg npSDT1xuEIOSLNt2RT2EbFrE8XRZoV29t1n7kg6GxXg

Requires:
    python-gobject: Python Bindings for GLib/GObject/GIO/GTK+
    usbguard: USB device authorization policy framework

@author @cyrinux, @maximbaz
@license BSD

SAMPLE OUTPUT
[
    {'full_text': '[Reject] ', 'urgent': True},
    {'full_text': 'USB Flash Drive ', 'urgent': True},
    {'full_text': '[Allow]', 'urgent': True}
]
"""

from threading import Thread
from gi.repository import GLib, Gio
import re

STRING_USBGUARD_DBUS = "start usbguard-dbus.service"


class Py3status:
    """
    """

    # available configuration parameters
    format = "{format_device}"
    format_button_allow = "\[Allow\]"
    format_button_reject = "\[Reject\]"
    format_device = "{format_button_reject} [{name}|{usb_id}] {format_button_allow}"
    format_device_separator = " "

    def post_config_hook(self):
        self.init = {
            "format_button": self.py3.get_placeholders_list(
                self.format_device, "format_button_*"
            ),
            "target": {"allow": 0, "reject": 2},
        }

        self.keys = [
            ("serial", re.compile(r"\S*serial \"(\S+)\"\S*")),
            ("policy", re.compile(r"^(\S+)")),
            ("usb_id", re.compile(r"id (\S+)")),
            ("name", re.compile(r"name \"(.*)\" hash")),
            ("hash", re.compile(r"hash \"(.*)\" parent-hash")),
            ("parent_hash", re.compile(r"parent-hash \"(.*)\" via-port")),
            ("port", re.compile(r"via-port \"(.*)\" with-interface")),
            ("interface", re.compile(r"with-interface \{ (.*) \}$")),
        ]

        self._init_dbus()

    def _init_dbus(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.proxy = Gio.DBusProxy.new_sync(
            self.bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.usbguard",
            "/org/usbguard/Devices",
            "org.usbguard.Devices",
            None,
        )
        for signal in ["DevicePolicyChanged", "DevicePresenceChanged"]:
            self.bus.signal_subscribe(
                None,
                "org.usbguard.Devices",
                signal,
                None,
                None,
                0,
                lambda *args: self.py3.update(),
            )

        thread = Thread(target=lambda: GLib.MainLoop().run())
        thread.daemon = True
        thread.start()

    def _get_devices(self):
        try:
            raw_devices = self.proxy.listDevices("(s)", "block")
        except Exception:
            raise Exception(STRING_USBGUARD_DBUS)

        devices = []
        for device_id, string in raw_devices:
            device = {"id": device_id}
            string = string.encode("latin-1").decode("unicode_escape")
            string = string.encode("latin-1").decode("utf-8")
            for name, regex in self.keys:
                value = regex.findall(string) or None
                if value:
                    value = value[0]
                device[name] = value
            devices.append(device)

        return devices

    def _format_device(self, devices):
        device_info = []
        for device in devices:
            for btn in self.init["format_button"]:
                composite = self.py3.safe_format(getattr(self, btn), device)
                device[btn] = self.py3.composite_update(
                    composite,
                    {"index": "{}/{}".format(device["id"], btn.split("_")[-1])},
                )

            device_info.append(self.py3.safe_format(self.format_device, device))

        format_device_separator = self.py3.safe_format(self.format_device_separator)
        format_device = self.py3.composite_join(format_device_separator, device_info)

        return format_device

    def usbguard(self):
        devices = self._get_devices()

        usbguard_data = {
            "device": len(devices),
            "format_device": self._format_device(devices),
        }

        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, usbguard_data),
            "urgent": True,
        }

    def on_click(self, event):
        if isinstance(event["index"], int):
            return

        device_id, policy_name = event["index"].split("/")
        policy = self.init["target"][policy_name]
        self.proxy.applyDevicePolicy("(uub)", int(device_id), policy, False)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
