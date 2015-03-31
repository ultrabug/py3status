# -*- coding: utf-8 -*-
"""
Display network speed and bandwidth usage.

Configuration parameters:
    - cache_timeout : 0 by default, you usually want continuous monitoring
    - low_* / med_* : coloration thresholds
    - nic : the network interface to monitor (defaults to eth0)

@author Shahin Azad <ishahinism at Gmail>
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
    """
    # available configuration parameters
    cache_timeout = 2
    low_speed = 30
    low_traffic = 400
    med_speed = 60
    med_traffic = 700
    nic = 'wlp2s0'

    def __init__(self):
        self.old_transmitted = 0
        self.old_received = 0

    def net_speed(self, i3s_output_list, i3s_config):
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

    def net_traffic(self, i3s_output_list, i3s_config):
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
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.net_speed([], config))
        print(x.net_traffic([], config))
        sleep(1)
