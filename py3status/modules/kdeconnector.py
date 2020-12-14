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
    format = "{name} {battery} ⚡ {state}"
    low_battery = "10"
}
```

@author Moritz Lüdecke

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

from pydbus import SessionBus


SERVICE_BUS = "org.kde.kdeconnect"
INTERFACE = SERVICE_BUS + ".device"
INTERFACE_DAEMON = SERVICE_BUS + ".daemon"
INTERFACE_BATTERY = INTERFACE + ".battery"
INTERFACE_NOTIFICATIONS = INTERFACE + ".notifications"
PATH = "/modules/kdeconnect"
DEVICE_PATH = PATH + "/devices"
UNKNOWN = "Unknown"
UNKNOWN_DEVICE = "unknown device"
UNKNOWN_SYMBOL = "?"


class Py3status:
    """
    """

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
        self._dev = None

    def _init_dbus(self):
        """
        Get the device id
        """
        _bus = SessionBus()

        if self.device_id is None:
            self.device_id = self._get_device_id(_bus)
            if self.device_id is None:
                return False

        try:
            self._dev = _bus.get(SERVICE_BUS, DEVICE_PATH + f"/{self.device_id}")
        except Exception:
            return False

        return True

    def _get_device_id(self, bus):
        """
        Find the device id
        """
        _dbus = bus.get(SERVICE_BUS, PATH)
        devices = _dbus.devices()

        if self.device is None and self.device_id is None and len(devices) == 1:
            return devices[0]

        for id in devices:
            self._dev = bus.get(SERVICE_BUS, DEVICE_PATH + f"/{id}")
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
            battery = {
                "charge": self._dev.charge(),
                "isCharging": self._dev.isCharging() == 1,
            }
        except Exception:
            return None

        return battery

    def _get_notifications(self):
        """
        Get notifications
        """
        try:
            notifications = {"activeNotifications": self._dev.activeNotifications()}
        except Exception:
            return None

        return notifications

    def _get_battery_status(self, battery):
        """
        Get the battery status
        """
        if battery["charge"] == -1:
            return (UNKNOWN_SYMBOL, UNKNOWN, "#FFFFFF")

        if battery["isCharging"]:
            status = self.status_chr
            color = self.py3.COLOR_GOOD
        else:
            status = self.status_bat
            color = self.py3.COLOR_DEGRADED

        if not battery["isCharging"] and battery["charge"] <= self.low_threshold:
            color = self.py3.COLOR_BAD

        if battery["charge"] > 99:
            status = self.status_full

        return (battery["charge"], status, color)

    def _get_notifications_status(self, notifications):
        """
        Get the notifications status
        """
        if notifications:
            size = len(notifications["activeNotifications"])
        else:
            size = 0
        status = self.status_notif if size > 0 else self.status_no_notif

        return (size, status)

    def _get_text(self):
        """
        Get the current metadatas
        """
        device = self._get_device()
        if device is None:
            return (UNKNOWN_DEVICE, self.py3.COLOR_BAD)

        if not device["isReachable"] or not device["isTrusted"]:
            return (
                self.py3.safe_format(
                    self.format_disconnected, {"name": device["name"]}
                ),
                self.py3.COLOR_BAD,
            )

        battery = self._get_battery()
        (charge, bat_status, color) = self._get_battery_status(battery)

        notif = self._get_notifications()
        (notif_size, notif_status) = self._get_notifications_status(notif)

        return (
            self.py3.safe_format(
                self.format,
                dict(
                    name=device["name"],
                    charge=charge,
                    bat_status=bat_status,
                    notif_size=notif_size,
                    notif_status=notif_status,
                ),
            ),
            color,
        )

    def kdeconnector(self):
        """
        Get the current state and return it.
        """
        if self._init_dbus():
            (text, color) = self._get_text()
        else:
            text = UNKNOWN_DEVICE
            color = self.py3.COLOR_BAD

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
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
