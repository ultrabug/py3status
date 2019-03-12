# -*- coding: utf-8 -*-
"""
Display network and IP address for newer Huwei modems.

It is tested for Huawei E3276 (usb-id 12d1:1506) aka Telekom Speed
Stick LTE III but may work on other devices too.

Configuration parameters:
    baudrate: There should be no need to configure this, but
        feel free to experiment.
        (default 115200)
    cache_timeout: How often we refresh this module in seconds.
        (default 5)
    consider_3G_degraded: If set to True, only 4G-networks will be
        considered 'good'; 3G connections are shown
        as 'degraded', which is yellow by default. Mostly
        useful if you want to keep track of where there
        is a 4G connection.
        (default False)
    format_down: What to display when the modem is not plugged in
        (default 'WWAN: down')
    format_error: What to display when modem can't be accessed.
        (default 'WWAN: {error}')
    format_no_service: What to display when the modem does not have a
        network connection. This allows to omit the (then
        meaningless) network generation.
        (default 'WWAN: {status} {ip}')
    format_up: What to display upon regular connection
        (default 'WWAN: {status} ({netgen}) {ip}')
    interface: The default interface to obtain the IP address
        from. For wvdial this is most likely ppp0.
        For netctl it can be different.
        (default 'ppp0')
    modem: The device to send commands to. (default '/dev/ttyUSB1')
    modem_timeout: The timespan between querying the modem and
        collecting the response.
        (default 0.4)

Color options:
    color_bad: Error or no connection
    color_degraded: Low generation connection eg 2G
    color_good: Good connection

Requires:
    netifaces: portable module to access network interface information
    pyserial: multiplatform serial port module for python

@author Timo Kohorst timo@kohorst-online.com
PGP: B383 6AE6 6B46 5C45 E594 96AB 89D2 209D DBF3 2BB5

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'WWAN: 4G 37.48.108.0'}

off
{'color': '#FF0000', 'full_text': u'WWAN: down'}
"""

import netifaces as ni
import os
import stat
import serial
from time import sleep


class Py3status:
    """
    """

    # available configuration parameters
    baudrate = 115200
    cache_timeout = 5
    consider_3G_degraded = False
    format_down = "WWAN: down"
    format_error = "WWAN: {error}"
    format_no_service = "WWAN: {status} {ip}"
    format_up = "WWAN: {status} ({netgen}) {ip}"
    interface = "ppp0"
    modem = "/dev/ttyUSB1"
    modem_timeout = 0.4

    def wwan_status(self):

        query = "AT^SYSINFOEX"
        target_line = "^SYSINFOEX"

        # Set up the highest network generation to display as degraded
        if self.consider_3G_degraded:
            degraded_netgen = 3
        else:
            degraded_netgen = 2

        response = {}
        response["cached_until"] = self.py3.time_in(self.cache_timeout)

        # Check if path exists and is a character device
        if os.path.exists(self.modem) and stat.S_ISCHR(os.stat(self.modem).st_mode):
            print("Found modem " + self.modem)
            try:
                ser = serial.Serial(
                    port=self.modem,
                    baudrate=self.baudrate,
                    # Values below work for my modem. Not sure if
                    # they neccessarily work for all modems
                    parity=serial.PARITY_ODD,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                )
                if ser.isOpen():
                    ser.close()
                ser.open()
                ser.write((query + "\r").encode())
                print("Issued query to " + self.modem)
                sleep(self.modem_timeout)
                n = ser.inWaiting()
                modem_response = ser.read(n)
                ser.close()
            except:  # noqa e722
                # This will happen...
                # 1) in the short timespan between the creation of the device
                # node and udev changing the permissions. If this message
                # persists, double check if you are using the proper device
                # file
                # 2) if/when you unplug the device
                print("Permission error")
                response["full_text"] = self.py3.safe_format(
                    self.format_error, dict(error="no access to " + self.modem)
                )
                response["color"] = self.py3.COLOR_BAD
                return response
            # Dissect response
            for line in modem_response.decode("utf-8").split("\n"):
                print(line)
                if line.startswith(target_line):
                    # Determine IP once the modem responds
                    ip = self._get_ip(self.interface)
                    if not ip:
                        ip = "no ip"
                    modem_answer = line.split(",")
                    netgen = len(modem_answer[-2]) + 1
                    netmode = modem_answer[-1].rstrip()[1:-1]
                    if netmode == "NO SERVICE":
                        response["full_text"] = self.py3.safe_format(
                            self.format_no_service, dict(status=netmode, ip=ip)
                        )
                        response["color"] = self.py3.COLOR_BAD
                    else:
                        response["full_text"] = self.py3.safe_format(
                            self.format_up,
                            dict(status=netmode, netgen=str(netgen) + "G", ip=ip),
                        )
                        if netgen <= degraded_netgen:
                            response["color"] = self.py3.COLOR_DEGRADED
                        else:
                            response["color"] = self.py3.COLOR_GOOD
                elif line.startswith("COMMAND NOT SUPPORT") or line.startswith("ERROR"):
                    response["color"] = self.py3.COLOR_BAD
                    response["full_text"] = self.py3.safe_format(
                        self.format_error, {"error": "unsupported modem"}
                    )
                else:
                    # Outputs can be multiline, so just try the next one
                    pass
        else:
            response["color"] = self.py3.COLOR_BAD
            response["full_text"] = self.format_down
        return response

    def _get_ip(self, interface):
        """
        Returns the interface's IPv4 address if device exists and has a valid
        ip address. Otherwise, returns an empty string
        """
        if interface in ni.interfaces():
            addresses = ni.ifaddresses(interface)
            if ni.AF_INET in addresses:
                return addresses[ni.AF_INET][0]["addr"]
        return ""


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
