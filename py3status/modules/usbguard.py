#!/usr/bin/env python3
from gi.repository import GLib
from pydbus import SystemBus

bus = SystemBus()
proxy = bus.get('org.usbguard')
proxy_devices = proxy[".Devices"]
devices_filter = '/org/usbguard/Devices'
loop = GLib.MainLoop()


def cb_server_signal_emission(*args):
    """
    Callback on emitting signal from server
    """
    print("Message: ", args)
    print("Data: ", str(args[4][4]))
    device = args[4]
    device_name = device[4]['name']
    device_id = device[0]
    print("Id: ", device_id)
    print("Name: ", device_name)


bus.subscribe(
    object=devices_filter,
    signal='DevicePresenceChanged',
    signal_fired=cb_server_signal_emission)

loop.run()
