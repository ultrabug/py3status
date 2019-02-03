# -*- coding: utf-8 -*-
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
        (default 'VPN: {name}|VPN: no')
    pidfile: Same as i3status pidfile, checked when check_pid is True.
        (default '/sys/class/net/vpn0/dev_id')

Format placeholders:
    {name} The name and/or status of the VPN.

Color options:
    color_bad: VPN connected
    color_good: VPN down

Requires:
    pydbus: Which further requires PyGi. Check your distribution's repositories.

@author Nathan Smith <nathan AT praisetopia.org>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'VPN: yes'}

off
{'color': '#FF0000', 'full_text': u'VPN: no'}
"""

from pydbus import SystemBus
from gi.repository import GObject
from threading import Thread
from os import path
from time import sleep


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    check_pid = False
    format = "VPN: {name}|VPN: no"
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
        loop = GObject.MainLoop()
        bus = SystemBus()
        manager = bus.get(".NetworkManager")
        manager.onPropertiesChanged = self._vpn_signal_handler

        # Loop forever
        loop.run()

    def _vpn_signal_handler(self, args):
        """Called on NetworkManager PropertiesChanged signal"""
        # Args is a dictionary of changed properties
        # We only care about changes in ActiveConnections
        active = "ActiveConnections"
        # Compare current ActiveConnections to last seen ActiveConnections
        if active in args.keys() and sorted(self.active) != sorted(args[active]):
            self.active = args[active]
            self.py3.update()

    def _get_vpn_status(self):
        """Returns None if no VPN active, Id if active."""
        # Sleep for a bit to let any changes in state finish
        sleep(0.3)
        # Check if any active connections are a VPN
        bus = SystemBus()
        ids = []
        for name in self.active:
            conn = bus.get(".NetworkManager", name)
            if conn.Vpn:
                ids.append(conn.Id)
        # No active VPN
        return ids

    def _check_pid(self):
        """Returns True if pidfile exists, False otherwise."""
        return path.isfile(self.pidfile)

    # Method run by py3status
    def vpn_status(self):
        """Returns response dict"""

        # Start signal handler thread if it should be running
        if not self.check_pid and not self.thread_started:
            self._start_handler_thread()

        # Set color_bad as default output. Replaced if VPN active.
        name = None
        color = self.py3.COLOR_BAD

        # If we are acting like the default i3status module
        if self.check_pid:
            if self._check_pid():
                name = "yes"
                color = self.py3.COLOR_GOOD

        # Otherwise, find the VPN name, if it is active
        else:
            vpn = self._get_vpn_status()
            if vpn:
                name = ", ".join(vpn)
                color = self.py3.COLOR_GOOD

        # Format and create the response dict
        full_text = self.py3.safe_format(self.format, {"name": name})
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
