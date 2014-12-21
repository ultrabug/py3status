# -*- coding: utf-8 -*-
"""
Display network information (Linux systems) in i3bar.

Copyright (C) <2013> <Shahin Azad [ishahinism at Gmail]>
"""

import subprocess
from time import time


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
    Configuration parameters:
        - cache_timeout : 0 by default, you usually want continuous monitoring
        - low_* / med_* : coloration thresholds
        - nic : the network interface to monitor (defaults to eth0)
    """
    # available configuration parameters
    cache_timeout = 0
    low_speed = 30
    low_traffic = 400
    med_speed = 60
    med_traffic = 700
    nic = 'eth0'

    def __init__(self):
        self.old_transmitted = 0
        self.old_received = 0

    def netSpeed(self, i3s_output_list, i3s_config):
        """Calculate network speed ('eth0' interface) and return it.  You can
        change the interface using 'self.nic' variable in
        'GetData' class.
        """
        data = GetData(self.nic)
        response = {'full_text': ''}

        received_bytes, transmitted_bytes = data.netBytes()
        dl_speed = (self.received_bytes - self.old_received) / 1024.
        up_speed = (self.transmitted_bytes - self.old_transmitted) / 1024.

        if dl_speed < self.low_speed:
            response['color'] = i3s_config['color_bad']
        elif dl_speed < self.med_speed:
            response['color'] = i3s_config['color_degraded']
        else:
            response['color'] = i3s_config['color_good']

        response['full_text'] = "LAN(Kb): {:5.1f}↓ {:5.1f}↑"\
            .format(dl_speed, up_speed)
        response['cached_until'] = time() + self.cache_timeout

        self.old_received = received_bytes
        self.old_transmitted = transmitted_bytes

        return response

    def traffic(self, i3s_output_list, i3s_config):
        """Calculate networks used traffic. Same as 'netSpeed' method you can
        change the interface.
        """
        data = GetData(self.nic)
        response = {'full_text': ''}

        received_bytes, transmitted_bytes = data.netBytes()
        download = received_bytes / 1024 / 1024.
        upload = transmitted_bytes / 1024 / 1024.
        total = download + upload

        if total < self.low_traffic:
            response['color'] = i3s_config['color_good']
        elif total < self.med_traffic:
            response['color'] = i3s_config['color_degraded']
        else:
            response['color'] = i3s_config['color_bad']

        response['full_text'] = "T(Mb): {:3.0f}↓ {:3.0f}↑ {:3.0f}↕".format(
            download,
            upload,
            total
        )

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.netSpeed([], {}))
        print(x.traffic([], {}))
        sleep(1)
