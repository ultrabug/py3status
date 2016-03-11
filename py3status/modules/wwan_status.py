# -*- coding: utf-8 -*-
"""
Display current network and ip address for newer Huwei modems.

It is tested for Huawei E3276 (usb-id 12d1:1506) aka Telekom Speed
Stick LTE III but may work on other devices, too.

DEPENDENCIES:
    netifaces:
    pyserial:

Configuration parameters:
    baudrate: There should be no need to configure this, but
        feel free to experiment.
        Default is 115200.
    cache_timeout: How often we refresh this module in seconds.
        Default is 5.
    consider_3G_degraded: If set to True, only 4G-networks will be
        considered 'good'; 3G connections are shown
        as 'degraded', which is yellow by default. Mostly
        useful if you want to keep track of where there
        is a 4G connection.
        Default is False.
    format_down: What to display when the modem is not plugged in
        Default is: 'WWAN: down'
    format_error: What to display when modem can't be accessed.
        Default is 'WWAN: {error}'
    format_no_service: What to display when the modem does not have a
        network connection. This allows to omit the then
        meaningless network generation. Therefore the
        default is 'WWAN: ({status}) {ip}'
    format_up: What to display upon regular connection
        Default is 'WWAN: ({status}/{netgen}) {ip}'
    interface: The default interface to obtain the IP address
        from. For wvdial this is most likely ppp0.
        For netctl it can be different.
        Default is: ppp0
    modem: The device to send commands to. Default is
    modem_timeout: The timespan betwenn querying the modem and
        collecting the response.
        Default is 0.4 (which should be sufficient)

@author Timo Kohorst timo@kohorst-online.com
PGP: B383 6AE6 6B46 5C45 E594 96AB 89D2 209D DBF3 2BB5
"""

import netifaces as ni
import os
import stat
import serial
from time import time, sleep


class Py3status:
    baudrate = 115200
    cache_timeout = 5
    consider_3G_degraded = False
    format_down = 'WWAN: down'
    format_error = 'WWAN: {error}'
    format_no_service = 'WWAN: {status} {ip}'
    format_up = 'WWAN: {status} ({netgen}) {ip}'
    interface = "ppp0"
    modem = "/dev/ttyUSB1"
    modem_timeout = 0.4

    def wwan_status(self, i3s_output_list, i3s_config):

        query = "AT^SYSINFOEX"
        target_line = "^SYSINFOEX"

        # Set up the highest network generation to display as degraded
        if self.consider_3G_degraded:
            degraded_netgen = 3
        else:
            degraded_netgen = 2

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
                # 1) in the short timespan between the creation of the device
                # node and udev changing the permissions. If this message
                # persists, double check if you are using the proper device
                # file
                # 2) if/when you unplug the device
                print("Permission error")
                response['full_text'] = self.format_error.format(
                    error="no access to " + self.modem)
                response['color'] = i3s_config['color_bad']
                return response
            # Dissect response
            for line in modem_response.decode("utf-8").split('\n'):
                print(line)
                if line.startswith(target_line):
                    # Determine IP once the modem responds
                    ip = self._get_ip(self.interface)
                    if not ip:
                        ip = "no ip"
                    modem_answer = line.split(',')
                    netgen = len(modem_answer[-2]) + 1
                    netmode = modem_answer[-1].rstrip()[1:-1]
                    if netmode == "NO SERVICE":
                        response['full_text'] = self.format_no_service.format(
                            status=netmode,
                            ip=ip)
                        response['color'] = i3s_config['color_bad']
                    else:
                        response['full_text'] = self.format_up.format(
                            status=netmode,
                            netgen=str(netgen) + "G",
                            ip=ip)
                        if netgen <= degraded_netgen:
                            response['color'] = i3s_config['color_degraded']
                        else:
                            response['color'] = i3s_config['color_good']
                elif line.startswith("COMMAND NOT SUPPORT") or line.startswith(
                        "ERROR"):
                    response['color'] = i3s_config['color_bad']
                    response['full_text'] = self.format_error.format(
                        error="unsupported modem")
                else:
                    # Outputs can be multiline, so just try the next one
                    pass
        else:
            print(self.modem + " not found")
            response['color'] = i3s_config['color_bad']
            response['full_text'] = self.format_down
        return response

    def _get_ip(self, interface):
        """
        Returns the interface's IPv4 address if device exists and has a valid
        ip address. Otherwise, returns an empty string
        """
        if interface in ni.interfaces():
            addresses = ni.ifaddresses(interface)
            if ni.AF_INET in addresses:
                return addresses[ni.AF_INET][0]['addr']
        return ""


if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
    }
    while True:
        print(x.wwan_status([], config))
        sleep(1)
