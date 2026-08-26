"""
Native reimplementation of i3status's `ethernet` module.

Gets the IP address and (if possible) the link speed of the given
ethernet interface. If no IPv4 address is available and an IPv6
address is, it will be displayed.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format_down: format used when interface has no address
        (default 'E: down')
    format_up: see placeholders below (default 'E: %ip (%speed)')
    interface: network interface to display; the special value
        '_first_' (case-insensitive) picks the first non-virtual,
        non-loopback ethernet interface that already has an IPv4 or
        IPv6 address (default '_first_')

Format placeholders:
    %interface the configured interface
    %ip the interface's IPv4 address, or IPv6 if it has none, or
        'no IP' if the interface is up but has no address
    %speed the negotiated link speed (eg '1 Gbit/s'), or '?' if it
        can't be determined

Color options:
    color_good: a usable IP address was found
    color_degraded: interface is up but has no address ('no IP')
    color_bad: interface has no address in either family

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Real i3status has no 'interface' config key - it comes from the
    section's title instead (eg `ethernet eth0 { }` gives
    interface="eth0"), with '_first_' special-cased the same way as
    this module's own default. This module exposes 'interface' as an
    ordinary config key instead, so it works with zero config; it's
    stripped automatically if the section resolves to the real
    i3status wrapper, since real i3status crashes on an unrecognized
    option.

    The link speed is read via the same ETHTOOL_GSET ioctl as the real
    i3status (ethtool.h), not by shelling out to the ethtool CLI.
    Verified against a real 100 Mbit/s link: matched the real i3status
    binary's own output exactly ("E: <ip> (100 Mbit/s)").

@author claude
"""

import ctypes
import fcntl
import socket
import struct

from py3status.i3status.helpers import resolve_cache_timeout
from py3status.i3status.network import get_ipv4_address, get_ipv6_address, resolve_first_interface

SIOCGIFFLAGS = 0x8913
SIOCETHTOOL = 0x8946
ETHTOOL_GSET = 0x00000001
IFF_RUNNING = 0x40


class _EthtoolCmd(ctypes.Structure):
    _fields_ = [
        ("cmd", ctypes.c_uint32),
        ("supported", ctypes.c_uint32),
        ("advertising", ctypes.c_uint32),
        ("speed", ctypes.c_uint16),
        ("duplex", ctypes.c_uint8),
        ("port", ctypes.c_uint8),
        ("phy_address", ctypes.c_uint8),
        ("transceiver", ctypes.c_uint8),
        ("autoneg", ctypes.c_uint8),
        ("mdio_support", ctypes.c_uint8),
        ("maxtxpkt", ctypes.c_uint32),
        ("maxrxpkt", ctypes.c_uint32),
        ("speed_hi", ctypes.c_uint16),
        ("eth_tp_mdix", ctypes.c_uint8),
        ("eth_tp_mdix_ctrl", ctypes.c_uint8),
        ("lp_advertising", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 2),
    ]


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format_down = "E: down"
    format_up = "E: %ip (%speed)"
    interface = "_first_"

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        if self.interface is not None and self.interface.lower() == "_first_":
            self.interface = resolve_first_interface("ethernet")
            self.py3.log(f"ethernet: '_first_' resolved to {self.interface!r}", "debug")

    @staticmethod
    def _is_running(interface):
        if interface is None:
            return False
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            ifreq = struct.pack("256s", interface.encode()[:15])
            result = fcntl.ioctl(sock.fileno(), SIOCGIFFLAGS, ifreq)
            flags = struct.unpack("H", result[16:18])[0]
            return bool(flags & IFF_RUNNING)
        except OSError:
            return False
        finally:
            sock.close()

    @staticmethod
    def _get_speed(interface):
        if interface is None:
            return "?"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            ecmd = _EthtoolCmd(cmd=ETHTOOL_GSET)
            ifreq = struct.pack("16sP", interface.encode()[:15], ctypes.addressof(ecmd))
            fcntl.ioctl(sock.fileno(), SIOCETHTOOL, ifreq)
        except OSError:
            return "?"
        finally:
            sock.close()

        speed = (ecmd.speed_hi << 16) | ecmd.speed
        if speed in (0, 0xFFFF, 0xFFFFFFFF):
            return "?"
        if speed == 2500:
            return "2.5 Gbit/s"
        if speed > 1000:
            return f"{speed // 1000} Gbit/s"
        return f"{speed} Mbit/s"

    def ethernet(self):
        ipv4 = get_ipv4_address(self.interface)
        ipv6 = get_ipv6_address(self.interface)
        running = self._is_running(self.interface)

        if ipv4 is not None:
            ip_address = ipv4
        elif ipv6 is not None:
            ip_address = ipv6
        elif running:
            ip_address = "no IP"
        else:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": self.format_down,
                "color": self.py3.COLOR_BAD,
            }

        color = self.py3.COLOR_DEGRADED if ip_address == "no IP" else self.py3.COLOR_GOOD
        full_text = (
            self.format_up.replace("%ip", ip_address)
            .replace("%speed", self._get_speed(self.interface))
            .replace("%interface", self.interface or "")
        )
        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
            "color": color,
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
