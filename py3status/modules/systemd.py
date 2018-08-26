# -*- coding: utf-8 -*-
"""
Display status of a service on your system.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module (default '{unit}: {status}')
    unit: specify the systemd unit to use (default 'dbus.service')

Format of status string placeholders:
    {unit} unit name, eg sshd
    {status} unit status, eg active, inactive, not-found

Color options:
    color_good: unit active
    color_bad: unit inactive
    color_degraded: unit not-found

Examples:
```
# show the status of vpn service
# left click to start, right click to stop
systemd vpn {
    unit = 'vpn.service'
    on_click 1 = 'exec sudo systemctl start vpn'
    on_click 3 = 'exec sudo systemctl stop vpn'
}
```

Requires:
    pydbus: pythonic dbus library

@author Adrian Lopez <adrianlzt@gmail.com>
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'sshd.service: active'}

inactive
{'color': '#FF0000', 'full_text': 'sshd.service: inactive'}

not-found
{'color': '#FFFF00', 'full_text': 'sshd.service: not-found'}
"""

from pydbus import SystemBus


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = '{unit}: {status}'
    unit = 'dbus.service'

    def post_config_hook(self):
        bus = SystemBus()
        systemd = bus.get('org.freedesktop.systemd1')
        self.systemd_unit = bus.get('.systemd1', systemd.LoadUnit(self.unit))

    def systemd(self):
        status = self.systemd_unit.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
        exists = self.systemd_unit.Get('org.freedesktop.systemd1.Unit', 'LoadState')

        if exists == 'not-found':
            color = self.py3.COLOR_DEGRADED
            status = exists
        elif status == 'active':
            color = self.py3.COLOR_GOOD
        elif status == 'inactive':
            color = self.py3.COLOR_BAD
        else:
            color = self.py3.COLOR_DEGRADED

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
            'full_text': self.py3.safe_format(
                self.format, {'unit': self.unit, 'status': status})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
