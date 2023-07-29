"""
Display information about your smartphone with KDEConnector.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 30)
    device: the device name, you need this if you have more than one device
        connected to your PC (default None)
    device_id: alternatively to the device name you can set your device id here
        (default None)
    format: see placeholders below
        (default '{name}{notif_status} {bat_status} {charge}%')
    format_disconnected: text if device is disconnected
        (default 'device disconnected')
    low_threshold: percentage value when text is twitch to color_bad
        (default 20)
    status_bat: text when battery is discharged (default '⬇')
    status_chr: text when device is charged (default '⬆')
    status_full: text when battery is full (default '☻')
    status_no_notif: text when you have no notifications (default '')
    status_notif: text when notifications are available (default ' ✉')

Format placeholders:
    {bat_status} battery state
    {charge} the battery charge
    {name} name of the device
    {notif_size} number of notifications
    {notif_status} shows if a notification is available or not
    {net_type} shows cell network type
    {net_strength} shows cell network strength

Color options:
    color_bad: Device unknown, unavailable
        or battery below low_threshold and not charging
    color_degraded: Connected and battery not charging
    color_good: Connected and battery charging

Requires:
    pydbus: pythonic d-bus library
    kdeconnect: adds communication between kde and your smartphone

Examples:
```
kdeconnector {
    device_id = "aa0844d33ac6ca03"
    format = "{name} {charge} {bat_status}"
    low_battery = "10"
}
```

@author Moritz Lüdecke, valdur55

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'Samsung Galaxy S6 \u2709 \u2B06 97%'}

charging
{'color': '#00FF00', 'full_text': u'Samsung Galaxy S6 \u2B06 97%'}

transition
{'color': '#FFFF00', 'full_text': u'Samsung Galaxy S6 \u2B07 93%'}

not-plugged
{'color': '#FF0000', 'full_text': u'Samsung Galaxy S6 \u2B07 92%'}

disconnected
{'color': '#FF0000', 'full_text': u'device disconnected'}

unknown
{'color': '#FF0000', 'full_text': u'unknown device'}
"""

import sys
from threading import Thread

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from pydbus import SessionBus

SERVICE_BUS = "org.kde.kdeconnect"
INTERFACE = SERVICE_BUS + ".device"
INTERFACE_DAEMON = SERVICE_BUS + ".daemon"
INTERFACE_BATTERY = INTERFACE + ".battery"
INTERFACE_NOTIFICATIONS = INTERFACE + ".notifications"
INTERFACE_CONN_REPORT = INTERFACE + ".connectivity_report"
PATH = "/modules/kdeconnect"
DEVICE_PATH = PATH + "/devices"
BATTERY_SUBPATH = "/battery"
CONN_REPORT_SUBPATH = "/connectivity_report"
NOTIFICATIONS_SUBPATH = "/notifications"
UNKNOWN = "Unknown"
UNKNOWN_DEVICE = "unknown device"
UNKNOWN_SYMBOL = "?"


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 30
    device = None
    device_id = None
    format = "{name}{notif_status} {bat_status} {charge}%"
    format_disconnected = "device disconnected"
    low_threshold = 20
    status_bat = "⬇"
    status_chr = "⬆"
    status_full = "☻"
    status_no_notif = ""
    status_notif = " ✉"

    def post_config_hook(self):
        self._bat = None
        self._con = None
        self._dev = None
        self._not = None

        self._result = {}

        self._signal_reachable_changed = None
        self._signal_battery = None
        self._signal_notifications = None
        self._signal_conn_report = None

        self._format_contains_notifications = self.py3.format_contains(
            self.format, ["notif_size", "notif_status"]
        )

        self._format_contains_connection_status = self.py3.format_contains(
            self.format, ["net_type", "net_strength"]
        )

        # start last
        self._kill = False
        self._dbus_loop = DBusGMainLoop()
        self._dbus = SessionBus()
        self._bus_initialized = self._init_dbus()
        self._start_listener()

        if self._bus_initialized:
            self._update_conn_info()
            self._update_notif_info()
            self._update_battery_info()

    def _start_loop(self):
        self._loop = GLib.MainLoop()
        GLib.timeout_add(1000, self._timeout)
        try:
            self._loop.run()
        except KeyboardInterrupt:
            # This branch is only needed for the test mode
            self._kill = True

    def _start_listener(self):
        self._signal_reachable_changed = self._dbus.con.signal_subscribe(
            sender=None,
            interface_name=INTERFACE,
            member="reachableChanged",
            object_path=None,
            arg0=None,
            flags=0,
            callback=self._reachable_on_change,
        )

        self._signal_battery = self._dbus.con.signal_subscribe(
            sender=None,
            interface_name=INTERFACE_BATTERY,
            member=None,
            object_path=None,
            arg0=None,
            flags=0,
            callback=self._battery_on_change,
        )

        if self._format_contains_notifications:
            self._signal_notifications = self._dbus.con.signal_subscribe(
                sender=None,
                interface_name=INTERFACE_NOTIFICATIONS,
                member=None,
                object_path=None,
                arg0=None,
                flags=0,
                callback=self._notifications_on_change,
            )

        if self._format_contains_connection_status:
            self._signal_conn_report = self._dbus.con.signal_subscribe(
                sender=None,
                interface_name=INTERFACE_CONN_REPORT,
                member=None,
                object_path=None,
                arg0=None,
                flags=0,
                callback=self._conn_report_on_change,
            )

        t = Thread(target=self._start_loop)
        t.daemon = True
        t.start()

    def _notifications_on_change(
        self, connection, owner, object_path, interface_name, event, new_value
    ):
        if self._is_current_device(object_path):
            self._update_notif_info()
            self.py3.update()

    def _reachable_on_change(
        self, connection, owner, object_path, interface_name, event, new_value
    ):
        if self._is_current_device(object_path):
            # Update only when device is connected
            if new_value[0]:
                self._update_battery_info()
                self._update_notif_info()
                self._update_conn_info()
            self.py3.update()

    def _battery_on_change(self, connection, owner, object_path, interface_name, event, new_value):
        if self._is_current_device(object_path):
            if event == "refreshed":
                if new_value[1] != -1:
                    self._set_battery_status(isCharging=new_value[0], charge=new_value[1])
            elif event == "stateChanged":
                self._set_battery_status(isCharging=new_value[0], charge=None)
            elif event == "chargeChanged":
                self._set_battery_status(isCharging=None, charge=new_value[0])
            else:
                self._update_battery_info()
            self.py3.update()

    def _conn_report_on_change(
        self, connection, owner, object_path, interface_name, event, new_value
    ):
        if self._is_current_device(object_path):
            if event == "refreshed":
                if (
                    self._result["net_type"] != new_value[0]
                    or self._result["net_strength_raw"] != new_value[1]
                ):
                    self._set_conn_status(net_type=new_value[0], net_strength=new_value[1])
                    self.py3.update()
            else:
                self._update_conn_info()
                self.py3.update()

    def _is_current_device(self, object_path):
        return self.device_id in object_path

    def _timeout(self):
        if self._kill:
            self._loop.quit()
            sys.exit(0)

    def _init_dbus(self):
        """
        Get the device id
        """
        if self.device_id is None:
            self.device_id = self._get_device_id()
            if self.device_id is None:
                return False

        try:
            self._dev = self._dbus.get(SERVICE_BUS, DEVICE_PATH + f"/{self.device_id}")
            try:
                self._bat = self._dbus.get(
                    SERVICE_BUS, DEVICE_PATH + f"/{self.device_id}" + BATTERY_SUBPATH
                )

                if self._format_contains_notifications:
                    self._not = self._dbus.get(
                        SERVICE_BUS,
                        DEVICE_PATH + f"/{self.device_id}" + NOTIFICATIONS_SUBPATH,
                    )
                else:
                    self._not = None
            except Exception:
                # Fallback to the old version
                self._bat = None
                self._not = None

            try:  # This plugin is released after kdeconnect version Mar 13, 2021
                if self._format_contains_connection_status:
                    self._con = self._dbus.get(
                        SERVICE_BUS,
                        DEVICE_PATH + f"/{self.device_id}" + CONN_REPORT_SUBPATH,
                    )
                else:
                    self._con = None
            except Exception:
                self._con = None

        except Exception:
            return False

        return True

    def _get_device_id(self):
        """
        Find the device id
        """
        _bus = self._dbus.get(SERVICE_BUS, PATH)
        devices = _bus.devices()

        if self.device is None and self.device_id is None and len(devices) == 1:
            return devices[0]

        for id in devices:
            self._dev = self._dbus.get(SERVICE_BUS, DEVICE_PATH + f"/{id}")
            if self.device == self._dev.name:
                return id

        return None

    def _get_isTrusted(self):
        if self._dev is None:
            return False

        try:
            # New method which replaced 'isPaired' in version 1.0
            return self._dev.isTrusted()
        except AttributeError:
            try:
                # Deprecated since version 1.0
                return self._dev.isPaired()
            except AttributeError:
                return False

    def _get_device(self):
        """
        Get the device
        """
        try:
            device = {
                "name": self._dev.name,
                "isReachable": self._dev.isReachable,
                "isTrusted": self._get_isTrusted(),
            }
        except Exception:
            return None

        return device

    def _get_battery(self):
        """
        Get the battery
        """
        try:
            if self._bat:
                charge = self._bat.charge
                isCharging = self._bat.isCharging
            else:
                charge = self._dev.charge()
                isCharging = self._dev.isCharging()
            battery = {
                "charge": charge,
                "isCharging": isCharging == 1,
            }
        except Exception:
            return {
                "charge": -1,
                "isCharging": None,
            }

        return battery

    def _get_conn(self):
        """
        Get the connection report
        """
        try:
            if self._con:
                # Possible values are -1 - 4
                strength = self._con.cellularNetworkStrength
                type = self._con.cellularNetworkType

                con_info = {
                    "strength": strength,
                    "type": type,
                }
            else:
                con_info = {
                    "strength": -1,
                    "type": "",
                }
        except Exception:
            return {
                "strength": -1,
                "type": "",
            }

        return con_info

    def _get_notifications(self):
        """
        Get notifications
        """
        try:
            if self._not:
                notifications = self._not.activeNotifications()
            else:
                notifications = self._dev.activeNotifications()
        except Exception:
            return []

        return notifications

    def _set_battery_status(self, isCharging, charge):
        """
        Get the battery status
        """
        if charge == -1:
            self._result["charge"] = UNKNOWN_SYMBOL
            self._result["bat_status"] = UNKNOWN
            self._result["color"] = "#FFFFFF"
            return

        if charge is not None:
            self._result["charge"] = charge

        if isCharging is not None:
            if isCharging:
                self._result["bat_status"] = self.status_chr
                self._result["color"] = self.py3.COLOR_GOOD
            else:
                self._result["bat_status"] = self.status_bat
                self._result["color"] = self.py3.COLOR_DEGRADED

            if (
                not isCharging
                and isinstance(self._result["charge"], int)
                and self._result["charge"] <= self.low_threshold
            ):
                self._result["color"] = self.py3.COLOR_BAD

        if charge is not None:
            if charge > 99:
                self._result["bat_status"] = self.status_full

    def _set_notifications_status(self, activeNotifications):
        """
        Get the notifications status
        """
        size = len(activeNotifications)
        self._result["notif_status"] = self.status_notif if size > 0 else self.status_no_notif
        self._result["notif_size"] = size

    def _set_conn_status(self, net_type, net_strength):
        """
        Get the conn status
        """
        self._result["net_strength_raw"] = net_strength
        self._result["net_strength"] = net_strength * 25 if net_strength > -1 else UNKNOWN_SYMBOL
        self._result["net_type"] = net_type

    def _get_text(self):
        """
        Get the current metadatas
        """
        device = self._get_device()
        if device is None:
            return (UNKNOWN_DEVICE, self.py3.COLOR_BAD)

        if not device["isReachable"] or not device["isTrusted"]:
            return (
                self.py3.safe_format(self.format_disconnected, {"name": device["name"]}),
                self.py3.COLOR_BAD,
            )

        return (
            self.py3.safe_format(
                self.format,
                dict(name=device["name"], **self._result),
            ),
            self._result.get("color"),
        )

    def _update_conn_info(self):
        if self._format_contains_connection_status:
            conn = self._get_conn()
            self._set_conn_status(net_type=conn["type"], net_strength=conn["strength"])

    def _update_notif_info(self):
        if self._format_contains_notifications:
            notif = self._get_notifications()
            self._set_notifications_status(notif)

    def _update_battery_info(self):
        battery = self._get_battery()
        self._set_battery_status(isCharging=battery["isCharging"], charge=battery["charge"])

    def kill(self):
        self._kill = True
        if self._signal_reachable_changed:
            self._dbus.con.signal_unsubscribe(self._signal_reachable_changed)

        if self._signal_battery:
            self._dbus.con.signal_unsubscribe(self._signal_battery)

        if self._signal_notifications:
            self._dbus.con.signal_unsubscribe(self._signal_notifications)

        if self._signal_conn_report:
            self._dbus.con.signal_unsubscribe(self._signal_conn_report)

    def kdeconnector(self):
        """
        Get the current state and return it.
        """
        if self._kill:
            raise KeyboardInterrupt

        if self._bus_initialized:
            (text, color) = self._get_text()
            cached_until = self.py3.CACHE_FOREVER

        else:
            text = UNKNOWN_DEVICE
            color = self.py3.COLOR_BAD
            cached_until = self.py3.time_in(self.cache_timeout)
            self._bus_initialized = self._init_dbus()
            if self._bus_initialized:
                self._update_conn_info()
                self._update_notif_info()
                self._update_battery_info()
                self.py3.update()

        response = {
            "cached_until": cached_until,
            "full_text": text,
            "color": color,
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
