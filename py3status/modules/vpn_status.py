"""
Drop-in replacement for i3status run_watch VPN module.

Expands on the i3status module by displaying the name of the connected vpn
using pydbus. Asynchronously updates on dbus signals unless check_pid is True.

Configuration parameters:
    cache_timeout: How often to refresh in seconds when check_pid is True.
        (default 10)
    check_pid: If True, act just like the default i3status module.
        (default False)
    format: Format of the output.
        (default 'VPN: {format_vpn}|VPN: no')
    format_vpn: display format for vpns (default '{name}')
    format_vpn_separator: show separator if more than one VPN (default ', ')
    pidfile: Same as i3status pidfile, checked when check_pid is True.
        (default '/sys/class/net/vpn0/dev_id')

Format placeholders:
    {format_vpn} format for VPNs

Format VPN placeholders:
    {name} The name and/or status of the VPN.
    {ipv4} The IPv4 address of the VPN
    {ipv6} The IPv6 address of the VPN

Color options:
    color_bad: VPN connected
    color_good: VPN down

Requires:
    dbus-python: to interact with dbus
    pygobject: which in turn requires libcairo2-dev, libgirepository1.0-dev

@author Nathan Smith <nathan AT praisetopia.org>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'VPN: vpn0, tun0'}

off
{'color': '#FF0000', 'full_text': u'VPN: no'}
"""

from pathlib import Path
from threading import Thread
from time import sleep

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    check_pid = False
    format = "VPN: {format_vpn}|VPN: no"
    format_vpn = "{name}"
    format_vpn_separator = ", "
    pidfile = "/sys/class/net/vpn0/dev_id"

    def post_config_hook(self):
        self.thread_started = False
        self.active = []

    def _start_handler_thread(self):
        """Called once to start the event handler thread."""
        # Create handler thread
        t = Thread(target=self._start_loop)
        t.daemon = True

        # Start handler thread
        t.start()
        self.thread_started = True

    def _start_loop(self):
        """Starts main event handler loop, run in handler thread t."""
        # Create our main loop, get our bus, and add the signal handler
        loop = DBusGMainLoop(set_as_default=True)
        dbus.set_default_main_loop(loop)

        bus = dbus.SystemBus()
        bus.add_signal_receiver(self._vpn_signal_handler, path="/org/freedesktop/NetworkManager")
        # Initialize the already active connections
        manager = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager",
        )
        interface = dbus.Interface(manager, "org.freedesktop.DBus.Properties")
        self.active = interface.Get("org.freedesktop.NetworkManager", "ActiveConnections")

        # Loop forever to listen for events
        loop = GLib.MainLoop()
        loop.run()

    def _vpn_signal_handler(self, *args):
        """Called on NetworkManager PropertiesChanged signal"""
        # Args is a dictionary of changed properties
        # We only care about changes in ActiveConnections
        active = "ActiveConnections"
        # Compare current ActiveConnections to last seen ActiveConnections
        for arg in args:
            if (
                isinstance(arg, dict)
                and active in arg
                and sorted(self.active) != sorted(arg[active])
            ):
                self.active = arg[active]
                self.py3.update()

    def _get_vpn_status(self):
        """Returns None if no VPN active, Id if active."""
        # Sleep for a bit to let any changes in state finish
        sleep(0.3)
        # Check if any active connections are a VPN
        bus = dbus.SystemBus()
        vpns = []
        for name in self.active:
            manager = bus.get_object(
                "org.freedesktop.NetworkManager",
                name,
            )
            interface = dbus.Interface(manager, "org.freedesktop.DBus.Properties")
            try:
                properties = interface.GetAll("org.freedesktop.NetworkManager.Connection.Active")
                if properties.get("Vpn") or properties.get("Type") in ("wireguard", "tun"):
                    ipv4, ipv6 = self._get_ips(bus, properties["Connection"])
                    vpns.append({"name": properties.get("Id"), "ipv4": ipv4, "ipv6": ipv6})
            except dbus.DBusException:
                # the connection id has disappeared
                pass

        return vpns

    def _get_ips(self, bus, connection_path):
        conn = bus.get_object("org.freedesktop.NetworkManager", connection_path)
        interface = dbus.Interface(conn, "org.freedesktop.NetworkManager.Settings.Connection")

        settings = interface.GetSettings()
        ipv4 = self._get_ip(settings["ipv4"])
        ipv6 = self._get_ip(settings["ipv6"])
        return ipv4, ipv6

    def _get_ip(self, ip_settings):
        address_data = ip_settings["address-data"]
        if address_data:
            return address_data[0].get("address")

        return None

    def _check_pid(self):
        """Returns True if pidfile exists, False otherwise."""
        return Path(self.pidfile).is_file()

    # Method run by py3status
    def vpn_status(self):
        """Returns response dict"""

        # Start signal handler thread if it should be running
        if not self.check_pid and not self.thread_started:
            self._start_handler_thread()

        vpns = []

        # If we are acting like the default i3status module
        if self.check_pid:
            if self._check_pid():
                format_vpn = self.py3.safe_format(self.format_vpn, {"name": "yes"})
                vpns.append(format_vpn)

        # Otherwise, find the VPN name, if it is active
        else:
            vpn_info = self._get_vpn_status()
            for vpn in vpn_info:
                format_vpn = self.py3.safe_format(self.format_vpn, vpn)
                vpns.append(format_vpn)

        color = self.py3.COLOR_GOOD if vpns else self.py3.COLOR_BAD

        # Format and create the response dict
        format_vpn_separator = self.py3.safe_format(self.format_vpn_separator)
        format_vpns = self.py3.composite_join(format_vpn_separator, vpns)
        full_text = self.py3.safe_format(self.format, {"format_vpn": format_vpns})
        response = {
            "full_text": full_text,
            "color": color,
            "cached_until": self.py3.CACHE_FOREVER,
        }

        # Cache forever unless in check_pid mode
        if self.check_pid:
            response["cached_until"] = self.py3.time_in(self.cache_timeout)
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
