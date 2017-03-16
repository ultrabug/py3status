# -*- coding: utf-8 -*-
"""
Check systemd unit status.

Check the status of a systemd unit.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 5)
    format: Format for module output (default "{unit}: {status}")
    unit: Name of the unit (default "dbus.service")

Format of status string placeholders:
    {unit} name of the unit
    {status} 'active', 'inactive' or 'not-found'

Color options:
    color_good: Unit active
    color_bad: Unit inactive
    color_degraded: Unit not found

Example:

```
# Check status of vpn service
# Start with left click
# Stop with right click
systemd vpn {
    unit = 'vpn.service'
    on_click 1 = "exec sudo systemctl start vpn"
    on_click 3 = "exec sudo systemctl stop vpn"
    format = '{unit} is {status}'
}
```

Requires:
    pydbus: python lib for dbus

@author Adrian Lopez <adrianlzt@gmail.com>
@license BSD
"""

from pydbus import SystemBus


class Py3status:
    # available configuration parameters
    cache_timeout = 5
    format = '{unit}: {status}'
    unit = 'dbus.service'

    def post_config_hook(self):
        bus = SystemBus()
        systemd = bus.get('org.freedesktop.systemd1')
        s_unit = systemd.LoadUnit(self.unit)
        self.systemd_unit = bus.get('.systemd1', s_unit)

    def check_status(self, i3s_output_list, i3s_config):
        """
        Ask dbus to get Status and loaded status for the unit
        """
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

        full_text = self.py3.safe_format(self.format, {'unit': self.unit, 'status': status})
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text,
            'color': color
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
