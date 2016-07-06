# -*- coding: utf-8 -*
"""
Display information of your android device over KDEConnector.

Configuration parameters:
    device: the device name, you need this if you have more than one device
            connected to your PC
    device_id: alternatively to the device name you can set your device id here
    format: see placeholders below
    format_disconnected: text if device is disconnected
    status_bat: text when battery is discharged
    status_chr: text when device is charged
    status_full: text when battery is full
    status_notif: text when notifications are available
    status_no_notif: text when you have no notifications
    low_threshold: percentage value when text is twitch to color_bad

Format of status string placeholders:
    {name} name of the device
    {notif_status} shows if a notification is available or nor
    {notif_size} number of notifications
    {bat_status} battery state
    {charge} the battery charge

i3status.conf example:

```
kdeconnector {
    device_id = "aa0844d33ac6ca03"
    format = "{name} {battery} ⚡ {state}"
    low_battery = "10"
}
```

Requires:
    pydbus
    kdeconnect

@author Moritz Lüdecke
"""

from time import time, sleep
import re
from pydbus import SessionBus


SERVICE_BUS = 'org.kde.kdeconnect'
INTERFACE = SERVICE_BUS + '.device'
INTERFACE_DAEMON = SERVICE_BUS + '.daemon'
INTERFACE_BATTERY = INTERFACE + '.battery'
INTERFACE_NOTIFICATIONS = INTERFACE + '.notifications'
PATH = '/modules/kdeconnect'
DEVICE_PATH = PATH + '/devices'
UNKNOWN = 'Unknown'
UNKNOWN_SYMBOL = '?'
UNKNOWN_DEVICE = 'unknown device'


class Py3status:
    """
    """
    # available configuration parameters
    device = None
    device_id = None
    format = '{name}{notif_status} {bat_status} {charge}%'
    format_disconnected = 'device disconnected'
    status_bat = '⬇'
    status_chr = '⬆'
    status_full = '☻'
    status_notif = ' ✉'
    status_no_notif = ''
    low_threshold = 20

    _dev = None

    def _init_dbus(self):
        """
        Get the device id
        """
        _bus = SessionBus()

        if self.device_id is None:
            self.device_id = self._get_device_id(_bus)
            if self.device_id is None:
                return False
        else:
            try:
                self._dev = _bus.get(SERVICE_BUS,
                                     DEVICE_PATH + '/%s' % self.device_id)
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
            self._dev = bus.get(SERVICE_BUS, DEVICE_PATH + '/%s' % id)
            if self.device == self._dev.name:
                return id

        return None

    def _get_device(self):
        """
        Get the device
        """
        try:
            device = {
                'name': self._dev.name,
                'isReachable': self._dev.isReachable,
                'isPaired': self._dev.isPaired,
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
                'charge': self._dev.charge(),
                'isCharging': self._dev.isCharging() == 1,
            }
        except Exception:
            return None

        return battery

    def _get_notifications(self):
        """
        Get notifications
        """
        try:
            notifications = {
                'activeNotifications': self._dev.activeNotifications()
            }
        except Exception:
            return None

        return notifications

    def _get_battery_status(self, i3s_config, battery):
        """
        Get the battery status
        """
        if battery['charge'] == -1:
            return (UNKNOWN_SYMBOL, UNKNOWN, '#FFFFFF')

        if battery['isCharging']:
            status = self.status_chr
            color = i3s_config['color_good']
        else:
            status = self.status_bat
            color = i3s_config['color_degraded']

        if not battery['isCharging'] and battery['charge'] <= self.low_threshold:
            color = i3s_config['color_bad']

        if battery['charge'] > 99:
            status = self.status_full

        return (battery['charge'], status, color)

    def _get_notifications_status(self, notifications):
        """
        Get the notifications status
        """
        size = len(notifications['activeNotifications'])
        status = self.status_notif if size > 0 else self.status_no_notif

        return (size, status)

    def _get_text(self, i3s_config):
        """
        Get the current metadatas
        """
        device = self._get_device()
        if device is None:
            return (UNKNOWN_DEVICE, i3s_config['color_bad'])

        if not device['isReachable'] or not device['isPaired']:
            return (self.format_disconnected.format(name=device['name']),
                    i3s_config['color_bad'])

        battery = self._get_battery()
        (charge, bat_status, color) = self._get_battery_status(i3s_config, battery)

        notif = self._get_notifications()
        (notif_size, notif_status) = self._get_notifications_status(notif)

        return (self.format.format(name=device['name'],
                                   charge=charge,
                                   bat_status=bat_status,
                                   notif_size=notif_size,
                                   notif_status=notif_status), color)

    def kdeconnector(self, i3s_output_list, i3s_config):
        """
        Get the current state and return it.
        """
        if self._init_dbus():
            (text, color) = self._get_text(i3s_config)
        else:
            text = UNKNOWN_DEVICE
            color = i3s_config['color_bad']

        response = {
            'cached_until': time() + i3s_config['interval'],
            'full_text': text,
            'color': color
        }
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    x = Py3status()
    config = {
        'interval': 5,
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.kdeconnector([], config))
        sleep(1)
