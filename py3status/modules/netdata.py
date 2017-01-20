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
"""

import subprocess


class GetData:
    """Get system status.
    """
    def __init__(self, nic):
        self.nic = nic

    def execCMD(self, cmd, arg):
        """Take a system command and its argument, then return the result.

        Arguments:
        - `cmd`: system command.
        - `arg`: argument.
        """
        result = subprocess.check_output([cmd, arg])
        return result

    def netBytes(self):
        """Execute 'cat /proc/net/dev', find the interface line (Default
        'eth0') and grab received/transmitted bytes.

        """
        net_data = self.execCMD('cat', '/proc/net/dev').decode('utf-8').split()
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
        if self.nic is None:
            # Read default gateway directly from /proc.
            with open("/proc/net/route") as fh:
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
        Calculate network speed ('eth0' interface) and return it.
        You can change the interface using 'nic' configuration parameter.
        """
        data = GetData(self.nic)
        response = {'full_text': ''}

        received_bytes, transmitted_bytes = data.netBytes()
        dl_speed = (received_bytes - self.old_received) / 1024.
        up_speed = (transmitted_bytes - self.old_transmitted) / 1024.

        if dl_speed < self.low_speed:
            response['color'] = self.py3.COLOR_BAD
        elif dl_speed < self.med_speed:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_GOOD

        response['full_text'] = "LAN(Kb): {:5.1f}↓ {:5.1f}↑"\
            .format(dl_speed, up_speed)
        response['cached_until'] = self.py3.time_in(self.cache_timeout)

        self.old_received = received_bytes
        self.old_transmitted = transmitted_bytes

        return response

    def net_traffic(self):
        """
        Calculate networks used traffic.
        You can change the interface using 'nic' configuration parameter.
        """
        data = GetData(self.nic)
        response = {'full_text': ''}

        received_bytes, transmitted_bytes = data.netBytes()
        download = received_bytes / 1024 / 1024.
        upload = transmitted_bytes / 1024 / 1024.
        total = download + upload

        if total < self.low_traffic:
            response['color'] = self.py3.COLOR_GOOD
        elif total < self.med_traffic:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD

        response['full_text'] = "T(Mb): {:3.0f}↓ {:3.0f}↑ {:3.0f}↕".format(
            download,
            upload,
            total
        )

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
