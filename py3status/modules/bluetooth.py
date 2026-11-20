r"""
Display bluetooth status.

Configuration parameters:
    format: display format for this module (default "{format_adapter}")
    format_adapter: display format for adapters (default "{format_device}")
    format_adapter_separator: show separator if more than one (default " ")
    format_device: display format for devices
        (default "\?if=connected&color=connected {alias}")
    format_device_separator: show separator if more than one (default " ")
    thresholds: specify color thresholds to use
        (default [(False, "bad"), (True, "good")])

Format placeholders:
    {format_adapter}      format for adapters
    {adapter}             number of adapters, eg 1

format_adapter placeholders:
    {format_device}       format for devices
    {device}              number of devices, eg 5
    {address}             eg, 00:00:00:00:00:00
    {addresstype}         eg, public
    {alias}               eg, thinkpad
    {class}               eg, 123456
    {discoverable}        eg, False
    {discoverabletimeout} eg, 0
    {discovering}         eg, False
    {modalias}            eg, usb:v1D68234ABCDEF5
    {name}                eg, z420
    {pairable}            eg, True
    {pairabletimeout}     eg, 0
    {path}                eg, /org/bluez/hci0
    {powered}             eg, True
    {uuids}               eg, []

format_device placeholders:
    {adapter}          eg, /org/bluez/hci0
    {address}          eg, 00:00:00:00:00:00
    {addresstype}      eg, public
    {alias}            eg, MSFT Mouse
    {battery}          eg, 95
    {class}            eg, 1234
    {connected}        eg, False
    {icon}             eg, input-mouse
    {legacypairing}    eg, False
    {modalias}         eg, usb:v1D68234ABCDEF5
    {name}             eg, Microsoft Bluetooth Notebook Mouse 5000
    {paired}           eg, True
    {servicesresolved} eg, False
    {trusted}          eg, True
    {uuids}            eg, []

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    pygobject: Python bindings for GObject Introspection

Examples:
```
# always display devices
bluetooth {
    format_device = "\?color=connected {alias}"
}

# set an alias via blueman-manager or bluetoothctl
# $ bluetoothctl
# [bluetooth] # devices
# [bluetooth] # connect 00:00:00:00:00:00
# [bluetooth] # set-alias "MSFT Mouse"

# display missing adapter (feat. request)
bluetooth {
    format = "\?if=adapter {format_adapter}|\?color=darkgray No Adapter"
}

# legacy default
bluetooth {
    format = "\?color=good BT: {format_adapter}|\?color=bad BT"
    format_device_separator = "\|"
}
```

@author jmdana, lasers
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'Microsoft Bluetooth Notebook Mouse 5000'}
"""

from threading import Thread

from gi.repository import Gio, GLib


class Py3status:
    """ """

    # available configuration parameters
    format = "{format_adapter}"
    format_adapter = "{format_device}"
    format_adapter_separator = " "
    format_device = r"\?if=connected&color=connected {alias}"
    format_device_separator = " "
    thresholds = [(False, "bad"), (True, "good")]

    def post_config_hook(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.names_and_matches = [
            ("adapters", "org.bluez.Adapter1"),
            ("devices", "org.bluez.Device1"),
        ]

        self.thresholds_init = {}
        for name in ["format", "format_adapter", "format_device"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(getattr(self, name))

        self.update_pending = False
        self._dbus_subscribe()
        thread = Thread(target=lambda: GLib.MainLoop().run())
        thread.daemon = True
        thread.start()

    def _dbus_subscribe(self):
        # subscribing by well-known name survives bluetoothd restarts
        bluez, dbus = "org.bluez", "org.freedesktop.DBus"
        manager, props = f"{dbus}.ObjectManager", f"{dbus}.Properties"
        for sender, iface, signal, arg0 in [
            (bluez, manager, "InterfacesAdded", None),
            (bluez, manager, "InterfacesRemoved", None),
            (bluez, props, "PropertiesChanged", f"{bluez}.Adapter1"),
            (bluez, props, "PropertiesChanged", f"{bluez}.Device1"),
            (bluez, props, "PropertiesChanged", f"{bluez}.Battery1"),
            # a crashed bluetoothd emits no InterfacesRemoved
            (dbus, dbus, "NameOwnerChanged", bluez),
        ]:
            self.bus.signal_subscribe(
                sender, iface, signal, None, arg0, Gio.DBusSignalFlags.NONE, self._on_signal
            )

    def _on_signal(self, bus, sender, path, iface, signal, params, *args):
        if signal == "PropertiesChanged":
            changed = params.unpack()[1]
            # discovery spams these; they are not displayed
            if set(changed) <= {"RSSI", "TxPower", "ManufacturerData", "ServiceData"}:
                return
        # coalesce bursts, eg during discovery
        if not self.update_pending:
            self.update_pending = True
            GLib.timeout_add(1000, self._on_timeout)

    def _on_timeout(self):
        self.update_pending = False
        self.py3.update()
        return False

    def _get_bluez_data(self):
        try:
            objects = self.bus.call_sync(
                "org.bluez",
                "/",
                "org.freedesktop.DBus.ObjectManager",
                "GetManagedObjects",
                None,
                None,
                Gio.DBusCallFlags.NO_AUTO_START,
                -1,
                None,
            ).unpack()[0]
        except GLib.Error as err:
            if not err.matches(Gio.dbus_error_quark(), Gio.DBusError.NAME_HAS_NO_OWNER):
                raise
            objects = {}

        temporary = {}

        for path, interfaces in sorted(objects.items()):
            interface_keys = interfaces.keys()
            for name, match in self.names_and_matches:
                if match in interface_keys:
                    interface = {k.lower(): v for k, v in interfaces[match].items()}
                    battery = interfaces.get("org.bluez.Battery1", {}).get("Percentage")
                    interface.update({"path": path, "uuids": [], "battery": battery})
                    temporary.setdefault(name, []).append(interface)
                    break

        for device in temporary.pop("devices", []):
            for adapter in temporary["adapters"]:
                if device["adapter"] == adapter["path"]:
                    adapter.setdefault("devices", []).append(device)
                    break

        return temporary

    def bluetooth(self):
        bluez_data = self._get_bluez_data()
        adapters = bluez_data.pop("adapters", [])
        new_adapter = []

        for adapter in adapters:
            devices = adapter.pop("devices", [])
            new_device = []

            for device in devices:
                for x in self.thresholds_init["format_device"]:
                    if x in device:
                        self.py3.threshold_get_color(device[x], x)

                new_device.append(self.py3.safe_format(self.format_device, device))

            format_device_separator = self.py3.safe_format(self.format_device_separator)
            format_device = self.py3.composite_join(format_device_separator, new_device)

            adapter.update({"format_device": format_device, "device": len(devices)})

            for x in self.thresholds_init["format_adapter"]:
                if x in adapter:
                    self.py3.threshold_get_color(adapter[x], x)

            new_adapter.append(self.py3.safe_format(self.format_adapter, adapter))

        format_adapter_separator = self.py3.safe_format(self.format_adapter_separator)
        format_adapter = self.py3.composite_join(format_adapter_separator, new_adapter)

        bluetooth_data = {"format_adapter": format_adapter, "adapter": len(adapters)}

        for x in self.thresholds_init["format"]:
            if x in bluetooth_data:
                self.py3.threshold_get_color(bluetooth_data[x], x)

        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, bluetooth_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
