# -*- coding: utf-8 -*-
"""
Display network speed and bandwidth usage.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 2)
    low_speed: threshold (default 30)
    low_traffic: threshold (default 400)
    med_speed: threshold (default 60)
    med_traffic: threshold (default 700)
    nic: the network interface to monitor (default None)

Color options:
    color_bad: Rate is below low threshold
    color_degraded: Rate is below med threshold
    color_good: Rate is med threshold or higher

@author Shahin Azad <ishahinism at Gmail>

SAMPLE OUTPUT
[
    {'color': '#FF0000', 'full_text': 'LAN(Kb):  16.9↓   5.2↑', 'separator': True},
    {'color': '#FF0000', 'full_text': 'T(Mb): 2264↓ 143↑ 2407↕'}
]
"""


class GetData:
    """
    Get system status.
    """
    def __init__(self, nic):
        self.nic = nic

    def netBytes(self):
        """
        Get bytes directly from /proc.
        """
        with open('/proc/net/dev') as fh:
            net_data = fh.read().split()
        interface_index = net_data.index(self.nic + ':')
        received_bytes = int(net_data[interface_index + 1])
        transmitted_bytes = int(net_data[interface_index + 9])
        return received_bytes, transmitted_bytes


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 2
    low_speed = 30
    low_traffic = 400
    med_speed = 60
    med_traffic = 700
    nic = None

    def __init__(self):
        self.old_transmitted = 0
        self.old_received = 0

    def post_config_hook(self):
        """
        Get network interface directly from /proc.
        """
        if self.nic is None:
            # Get default gateway directly from /proc.
            with open('/proc/net/route') as fh:
                for line in fh:
                    fields = line.strip().split()
                    if fields[1] == '00000000' and int(fields[3], 16) & 2:
                        self.nic = fields[0]
                        break
            if self.nic is None:
                self.nic = 'lo'
                self.py3.notify_user(
                    'netdata: cannot find a nic to use. selected nic: lo instead.'
                )
            self.py3.log('selected nic: %s' % self.nic)

    def net_speed(self):
        """
        Calculate network speed.
        """
        data = GetData(self.nic)

        received_bytes, transmitted_bytes = data.netBytes()
        dl_speed = (received_bytes - self.old_received) / 1024.
        up_speed = (transmitted_bytes - self.old_transmitted) / 1024.

        if dl_speed < self.low_speed:
            color = self.py3.COLOR_BAD
        elif dl_speed < self.med_speed:
            color = self.py3.COLOR_DEGRADED
        else:
            color = self.py3.COLOR_GOOD

        net_speed = "LAN(Kb): {:5.1f}↓ {:5.1f}↑".format(dl_speed, up_speed)
        self.old_received = received_bytes
        self.old_transmitted = transmitted_bytes

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
            'full_text': net_speed
        }

    def net_traffic(self):
        """
        Calculate networks used traffic.
        """
        data = GetData(self.nic)

        received_bytes, transmitted_bytes = data.netBytes()
        download = received_bytes / 1024 / 1024.
        upload = transmitted_bytes / 1024 / 1024.
        total = download + upload

        if total < self.low_traffic:
            color = self.py3.COLOR_GOOD
        elif total < self.med_traffic:
            color = self.py3.COLOR_DEGRADED
        else:
            color = self.py3.COLOR_BAD

        net_traffic = "T(Mb): {:3.0f}↓ {:3.0f}↑ {:3.0f}↕".format(download, upload, total)

        return {
            'color': color,
            'full_text': net_traffic
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
