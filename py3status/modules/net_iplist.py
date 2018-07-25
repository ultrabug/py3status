# -*- coding: utf-8 -*-
"""
Display network interfaces and IP addresses.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 30)
    format: display format for this module
        (default '\?color=interface [{format_interface}|\?show no interfaces]')
    format_interface: display format for network interfaces
        (default '\?if=connected {name}:[ {format_ip4}][ {format_ip6}]')
    format_interface_separator: show separator if more than one (default ' ')
    format_ip4: display format for IPv4 addresses (default '{ip}')
    format_ip4_separator: show separator if more than one (default ', ')
    format_ip6: display format for IPv6 addresses (default '{ip}')
    format_ip6_separator: show separator if more than one (default ', ')
    interface_blacklist: specify a list of interfaces to ignore (default ['lo'])
    ip_blacklist: specify a list of IP addresses to ignore (default [])
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (1, 'good')])
    use_sudo: use sudo to run ip, make sure to allow ip some root rights
        without a password by adding a sudoers entry, eg...
        '<user> ALL=(ALL) NOPASSWD:/sbin/ip address show' (default False)

Notes:
    `interface_blacklist` and `ip_blacklist` accepts shell-style wildcards.

Format placeholders:
    {interface} number of network interfaces
    {format_interface} format for network interfaces

format_interface placeholders:
    {name} interface name, eg eno1
    {format_ip4} format for IPv4 addresses
    {format_ip6} format for IPv6 addresses
    {ip4} number of IPv4 addresses
    {ip6} number of IPv6 addresses
    {ip} number of IP addresses
    {connected} a boolean based on interface data

format_ip4 placeholders:
    {ip} IPv4 address, eg 192.168.1.103

format_ip6 placeholders:
    {ip} IPv6 address, eg fe80::d625:7ea8:e729:716c/64

Color thresholds:
    format:
        interface: print color based on number of network interfaces
    format_interface:
        ip: print color based on number of IP addresses
        ip4: print color based on number of IPv4 addresses
        ip6: print color based on number of IPv6 addresses

Requires:
    iproute2: show/manipulate routing, devices, policy routing and tunnels

Examples:
```
# block loopback addresses
net_iplist {
    interface_blacklist = []
    ip_blacklist = ['127.*', '::1']
}

# show colorized ipv4 interfaces
net_iplist {
    format = '{format_interface}'
    format_interface = '[\?color=ip {name}][ {format_ip4}]'
}
```

@author guiniol, lasers

SAMPLE OUTPUT
[
    {'color': '#00FF00', 'full_text': u'wls1: 192.168.1.3 '},
    {'color': '#00FF00', 'full_text': u'fe80::f861:44bd:694a:b99c'},
]
"""

import re
from fnmatch import fnmatch


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 30
    format = '\?color=interface [{format_interface}|\?show no interfaces]'
    format_interface = '\?if=connected {name}:[ {format_ip4}][ {format_ip6}]'
    format_interface_separator = ' '
    format_ip4 = '{ip}'
    format_ip4_separator = ', '
    format_ip6 = '{ip}'
    format_ip6_separator = ', '
    interface_blacklist = ['lo']
    ip_blacklist = []
    thresholds = [(0, 'bad'), (1, 'good')]
    use_sudo = False

    def post_config_hook(self):
        self.re_interface = re.compile(r'\d+: (?P<interface>\w+):')
        self.re_ip4 = re.compile(r'\s+inet (?P<ip4>[\d\.]+)(?:/| )')
        self.re_ip6 = re.compile(r'\s+inet6 (?P<ip6>[\da-f:]+)(?:/| )')
        self.ip_command = ['ip', 'address', 'show']

        # use sudo?
        if self.use_sudo:
            self.ip_command[0:0] = ['sudo', '-n']

        self.init = {}
        for ip in ['ip4', 'ip6']:
            x = 'count_{}'.format(ip)
            self.init[x] = self.py3.format_contains(self.format_interface, ip)
            x = 'format_{}'.format(ip)
            self.init[x] = self.py3.format_contains(getattr(self, x), 'ip') and (
                self.py3.format_contains(self.format_interface, x)
            )

    def _blacklist(self, string, blacklist):
        for ignore in blacklist:
            if fnmatch(string, ignore):
                return True
        return False

    def _get_ip_data(self):
        ip_data = self.py3.command_output(self.ip_command)

        new_data = {}
        for line in ip_data.splitlines():
            interface = self.re_interface.match(line)
            if interface:
                current_interface = interface.group('interface')
                new_data[current_interface] = {}
                continue

            ip4 = self.re_ip4.match(line)
            if ip4:
                new_data.setdefault(current_interface, {}).setdefault(
                    'ip4', []).append(ip4.group('ip4'))
                continue

            ip6 = self.re_ip6.match(line)
            if ip6:
                new_data.setdefault(current_interface, {}).setdefault(
                    'ip6', []).append(ip6.group('ip6'))
                continue

        return new_data

    def net_iplist(self):
        new_interface = []
        count_interface = 0

        ip_data = self._get_ip_data()

        for interface, ips in ip_data.items():
            if self._blacklist(interface, self.interface_blacklist):
                continue

            connected = False

            format_ip4 = None
            new_ip4 = []
            count_ip4 = 0
            if self.init['format_ip4'] or self.init['count_ip4']:
                for ip4 in ips.get('ip4', []):
                    if not self._blacklist(ip4, self.ip_blacklist):
                        connected = True
                        count_ip4 += 1
                        if self.init['format_ip4']:
                            new_ip4.append(self.py3.safe_format(
                                self.format_ip4, {'ip': ip4}))

            if self.init['format_ip4']:
                format_ip4_separator = self.py3.safe_format(
                    self.format_ip4_separator)
                format_ip4 = self.py3.composite_join(
                    format_ip4_separator, new_ip4)

            format_ip6 = None
            new_ip6 = []
            count_ip6 = 0
            if self.init['format_ip6'] or self.init['count_ip6']:
                for ip6 in ips.get('ip6', []):
                    if not self._blacklist(ip6, self.ip_blacklist):
                        connected = True
                        count_ip6 += 1
                        if self.init['format_ip6']:
                            new_ip6.append(self.py3.safe_format(
                                self.format_ip6, {'ip': ip6}))

            if self.init['format_ip6']:
                format_ip6_separator = self.py3.safe_format(
                    self.format_ip6_separator)
                format_ip6 = self.py3.composite_join(
                    format_ip6_separator, new_ip6)

            if connected:
                count_interface += 1

            count_ip = count_ip4 + count_ip6

            if self.thresholds:
                self.py3.threshold_get_color(count_ip, 'ip')
                self.py3.threshold_get_color(count_ip4, 'ip4')
                self.py3.threshold_get_color(count_ip6, 'ip6')

            new_interface.append(
                self.py3.safe_format(
                    self.format_interface,
                    {
                        'name': interface,
                        'format_ip4': format_ip4,
                        'format_ip6': format_ip6,
                        'connected': connected,
                        'ip': count_ip,
                        'ip4': count_ip4,
                        'ip6': count_ip6,
                    }
                )
            )

        self.py3.threshold_get_color(count_interface, 'interface')

        # interface
        format_interface_separator = self.py3.safe_format(
            self.format_interface_separator)
        format_interface = self.py3.composite_join(
            format_interface_separator, new_interface)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {
                    'format_interface': format_interface,
                    'interface': count_interface
                }
            )
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
