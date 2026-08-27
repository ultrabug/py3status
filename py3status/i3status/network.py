"""
Shared network-interface helpers for the native i3status-compatible
modules (ethernet, wireless, ipv6).
"""

import fcntl
import ipaddress
import os
import socket
import struct

SIOCGIFADDR = 0x8915
PROBE_ADDRESS = "2001:7fd::1"  # k.root-servers.net anycast address


def get_ipv4_address(interface):
    if interface is None:
        return None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ifreq = struct.pack("256s", interface.encode()[:15])
        result = fcntl.ioctl(sock.fileno(), SIOCGIFADDR, ifreq)
        return socket.inet_ntoa(result[20:24])
    except OSError:
        return None
    finally:
        sock.close()


def _iter_inet6():
    """Yield (address, interface) pairs from /proc/net/if_inet6, or nothing
    if it's unreadable."""
    try:
        with open("/proc/net/if_inet6") as f:
            for line in f:
                parts = line.split()
                if len(parts) == 6:
                    yield str(ipaddress.IPv6Address(bytes.fromhex(parts[0]))), parts[5]
    except OSError:
        # /proc/net/if_inet6 unreadable - treat the same as "nothing found"
        pass


def get_ipv6_address(interface):
    if interface is None:
        return None
    for address, iface in _iter_inet6():
        if iface == interface:
            return address
    return None


def get_ipv6_iface(address):
    """Return the interface a given IPv6 address is assigned to, or None."""
    for candidate, iface in _iter_inet6():
        if candidate == address:
            return iface
    return None


def get_outbound_ipv6_address():
    """
    Return the globally routable IPv6 address this machine would use to
    reach the internet, or None with no IPv6 connectivity.

    Determined by asking the kernel which local address it would use to
    reach a known-global IPv6 address (PROBE_ADDRESS) - a UDP "connect"
    that never actually sends a packet, just makes the kernel pick a
    route. No subprocess, no packets sent.
    """
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    try:
        sock.connect((PROBE_ADDRESS, 53))
        return sock.getsockname()[0].split("%")[0]
    except OSError:
        return None
    finally:
        sock.close()


def _iface_devtype(ifname):
    try:
        with open(f"/sys/class/net/{ifname}/uevent") as f:
            for line in f:
                if line.startswith("DEVTYPE="):
                    return line.strip().split("=", 1)[1]
    except OSError:
        # interface's uevent file unreadable/gone - treat as "no DEVTYPE"
        pass
    return None


def _iface_net_type(ifname):
    devtype = _iface_devtype(ifname)
    if devtype == "wlan":
        return "wireless"
    if devtype is None:
        # matches i3status: no DEVTYPE line defaults to ethernet
        return "ethernet"
    return "other"


def _iface_is_virtual(ifname):
    try:
        target = os.path.realpath(f"/sys/class/net/{ifname}")
    except OSError:
        return False
    return target.startswith("/sys/devices/virtual/")


def resolve_first_interface(net_type):
    """
    Find the first non-loopback, non-virtual interface of net_type
    ('wireless' or 'ethernet') that already has an IPv4 or IPv6 address.

    Matches i3status's `_first_` special interface name (used the same
    way for both the ethernet and wireless modules).
    """
    try:
        names = sorted(os.listdir("/sys/class/net"))
    except OSError:
        return None
    for name in names:
        if name == "lo" or name.startswith("lo:"):
            continue
        if _iface_is_virtual(name):
            continue
        if _iface_net_type(name) != net_type:
            continue
        if get_ipv4_address(name) is not None or get_ipv6_address(name) is not None:
            return name
    return None
