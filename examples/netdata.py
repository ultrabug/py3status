# -*- coding: utf-8 -*-

# netdata

# Netdata is a module uses great Py3status (i3status wrapper) to
# display network information (Linux systems) in i3bar.
# For more information read:
# i3wm homepage: http://i3wm.org
# py3status homepage: https://github.com/ultrabug/py3status

# Copyright (C) <2013> <Shahin Azad [ishahinism at Gmail]>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# ----------------------------------------------------------------- #
# Notes:
# 1. netdata will check 'eth0' interface by default. You can
# change it by changing 'self.net_interface' variable in 'GetData'
# class.
# 2. Colors are depended on strict specification in traffic/netspeed methods.
# You can change them by manipulating conditions.

import subprocess
from time import time

# Method 'netSpeed' will use this variables to calculate downloaded
# bytes in last second.  Initializing this variables globally is
# necessary since we can't use __init__ method in Py3Status class.
old_transmitted, old_received = 0, 0


class GetData:
    """Get system status

    """
    def __init__(self):
        # You can change it to another interface.
        # It'll be used for grabbing net interface data.
        self.net_interface = 'eth0'

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
        net_data = self.execCMD('cat', '/proc/net/dev').split()
        interface_index = net_data.index(self.net_interface + ':')
        received_bytes = int(net_data[interface_index + 1])
        transmitted_bytes = int(net_data[interface_index + 9])

        return received_bytes, transmitted_bytes


class Py3status:
    """
    System status in i3bar
    """
    def netSpeed(self, json, i3status_config):
        """Calculate network speed ('eth0' interface) and return it.  You can
        change the interface using 'self.net_interface' variable in
        'GetData' class.

        """
        data = GetData()
        response = {'full_text': '', 'name': 'net_speed'}

        global old_received
        global old_transmitted

        received_bytes, transmitted_bytes = data.netBytes()
        dl_speed = (received_bytes - old_received) / 1024.
        up_speed = (transmitted_bytes - old_transmitted) / 1024.

        if dl_speed < 30:
            response['color'] = i3status_config['color_bad']
        elif dl_speed < 60:
            response['color'] = i3status_config['color_degraded']
        else:
            response['color'] = i3status_config['color_good']

        response['full_text'] = "LAN(Kb): {:5.1f}↓ {:5.1f}↑"\
            .format(dl_speed, up_speed)
        response['cached_until'] = time()

        old_received, old_transmitted = received_bytes, transmitted_bytes
        return (0, response)

    def traffic(self, json, i3status_config):
        """Calculate networks used traffic. Same as 'netSpeed' method you can
        change the interface.

        """
        data = GetData()
        response = {'full_text': '', 'name': 'traffic'}

        received_bytes, transmitted_bytes = data.netBytes()
        download = received_bytes / 1024 / 1024.
        upload = transmitted_bytes / 1024 / 1024.
        total = download + upload

        if total < 400:
            response['color'] = i3status_config['color_good']
        elif total < 700:
            response['color'] = i3status_config['color_degraded']
        else:
            response['color'] = i3status_config['color_bad']

        response['full_text'] = "T(Mb): {:3.0f}↓ {:3.0f}↑ {:3.0f}↕"\
            .format(download, upload, total)

        return (1, response)
