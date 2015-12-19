# -*- coding: utf-8 -*-
"""
Display current network and ip address for newer Huwei modems. It
is tested for Huawei E3276 (usb-id 12d1:1506) aka Telekom Speed
Stick LTE III

DEPENDENCIES:
    - netifaces
    - pyserial

Configuration parameters:
    - baudrate      : Default is 115200. There should be no need
                      to configure this, but feel free to experiment
    - cache_timeout : How often we refresh this module in seconds.
                      Default is 5.
    - interface     : The default interface to obtain the IP address
                      from. For wvdial this is most likely ppp0
                      (default), for netctl it can be different. If
                      show_ip is false, then this settings has no
                      effect
    - modem         : The device to send commands to. Default is
    - modem_timeout : The timespan betwenn querying the modem and
                      collecting the response. 0.2 seconds has turned
                      out to work for my E3276. If you do not get any
                      output, consider increasing the value in 0.1
                      second steps
                      /dev/ttyUSB1, which should be fine for most
                      USB modems
    - prefix        : Default is "WWAN: ".
    - show_ip       : Enable or disable IP address display for the
                      configured interface (see below). Default is
                      true

@author Timo Kohorst timo@kohorst-online.com
PGP: B383 6AE6 6B46 5C45 E594 96AB 89D2 209D DBF3 2BB5
"""

import subprocess
import netifaces as ni
import os
import stat
import serial
from time import time, sleep


class Py3status:
    baudrate = 115200
    cache_timeout = 5
    interface = "ppp0"
    modem = "/dev/ttyUSB1"
    modem_timeout = 0.2
    prefix = "WWAN: "
    show_ip = True

    def wwan_status(self, i3s_output_list, i3s_config):

        query = "AT^SYSINFOEX"
        target_line = "^SYSINFOEX"
        noipstring = "no ip"

        response = {}
        response['cached_until'] = time() + self.cache_timeout
        # Check if path exists and is a character device
        if os.path.exists(self.modem) and stat.S_ISCHR(os.stat(
                self.modem).st_mode):
            print("Found modem " + self.modem)
            try:
                ser = serial.Serial(
                    port=self.modem,
                    baudrate=self.baudrate,
                    # Values below work for my modem. Not sure if
                    # they neccessarily work for all modems
                    parity=serial.PARITY_ODD,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS)
                if ser.isOpen():
                    ser.close()
                ser.open()
                ser.write((query + "\r").encode())
                print("Issued query to " + self.modem)
                sleep(self.modem_timeout)
                n = ser.inWaiting()
                modem_response = ser.read(n)
                ser.close()
            except:
                # This will happen...
                # 1) in the short timespan between the creation of the device node
                # and udev changing the permissions. If this message persists,
                # double check if you are using the proper device file
                # 2) if/when you unplug the device
                PermissionError
                print("Permission error")
                response['color'] = i3s_config['color_bad']
                response[
                    'full_text'] = self.prefix + "no access to " + self.modem
                return response
            # Dissect response
            for line in modem_response.decode("utf-8").split('\n'):
                print(line)
                if line.startswith(target_line):
                    netmode = line.split(',')[-1].rstrip()[1:-1]
                    # Query IP address if desired
                    if self.show_ip:
                        ip_addr = noipstring
                        if self.interface in ni.interfaces():
                            addresses = ni.ifaddresses(self.interface)
                            if ni.AF_INET in addresses:
                                ip_addr = addresses[ni.AF_INET][0]['addr']

                    if netmode == "NO SERVICE":
                        response['color'] = i3s_config['color_bad']
                        if ip_addr != noipstring:
                            # Merely downgrade color to degraded if we still have an IP
                            # address, but there is no service
                            response['color'] = i3s_config['color_degraded']
                    elif netmode == "LTE":
                        response['color'] = i3s_config['color_good']
                    else:
                        response['color'] = i3s_config['color_degraded']
                    response[
                        'full_text'] = self.prefix + "(" + netmode + ")"
                    if self.show_ip:
                        response['full_text'] += " " + ip_addr
                    return response
                elif line.startswith("COMMAND NOT SUPPORT") or line.startswith(
                        "ERROR"):
                    response['full_text'] = self.prefix + "unsupported modem"
                    response['color'] = i3s_config['color_bad']

        else:
            print(self.modem + " not found")
            response['full_text'] = self.prefix + "down"
            response['color'] = i3s_config['color_bad']
        return response


if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
    }
    while True:
        print(x.wwan_status([], config))
        sleep(1)
