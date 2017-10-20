# -*- coding: utf-8 -*-
"""
Display list of network interfaces and IP addresses.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 30)
    format: display format for this module
        (default '\?color=count [{format_interface}|\?show no connection]')
    format_interface: display format for network interfaces
        (default '\?if=is_connected {interface}:[ {format_ip4}][ {format_ip6}]')
    format_interface_separator: show separator if more than one (default ' ')
    format_ip4: display format for IPv4 addresses (default '{ip4}')
    format_ip4_separator: show separator if more than one (default ', ')
    format_ip6: display format for IPv6 addresses (default '{ip6}')
    format_ip6_separator: show separator if more than one (default ', ')
    interface_blacklist: specify a list of interfaces to ignore.
        accepts shell-style wildcards.
        (default ['lo'])
    ip_blacklist: specify a list of IPs to ignore.
        accepts shell-style wildcards.
        (default [])
    thresholds: specify color thresholds to use.
        (default [(0, 'bad'), (1, 'good')])

Format placeholders:
    {count} number of connections
    {format_interface} format for network interfaces

format_interface placeholders:
    {interface} interface name, eg eno1
    {format_ip4} format for IPv4 addresses
    {format_ip6} format for IPv6 addresses
    {is_connected} a boolean based on interface data

format_ip4 placeholders:
    {ip4} IPv4 address, eg 192.168.1.103

format_ip6 placeholders:
    {ip6} IPv6 address, eg fe80::d625:7ea8:e729:716c/64

Color thresholds:
    count: print color based on number of connections
    count_interface: print color based on number of connections

Requires:
    iproute2: show/manipulate routing, devices, policy routing and tunnels

Examples:
```
# ask @guiniol for a description
net_iplist {
    interface_blacklist = []
    ip_blacklist = ['127.*', '::1']
}

# show colorized ipv4 interfaces
net_iplist {
    format = '{format_interface}'
    format_interface = '[\?color=count_interface {interface}][ {ip4}]'
}
```

@author guiniol, lasers

SAMPLE OUTPUT
{'color': '#00FF00',
 'full_text': u'wls1: 192.168.1.3 fe80::f861:44bd:694a:b99c'}
"""


import re
from fnmatch import fnmatch


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 30
    format = '\?color=count [{format_interface}|\?show no connection]'
    format_interface = '\?if=is_connected {interface}:[ {format_ip4}][ {format_ip6}]'
    format_interface_separator = ' '
    format_ip4 = '{ip4}'
    format_ip4_separator = ', '
    format_ip6 = '{ip6}'
    format_ip6_separator = ', '
    interface_blacklist = ['lo']
    ip_blacklist = []
    thresholds = [(0, 'bad'), (1, 'good')]

    def post_config_hook(self):
        self.interface_re = re.compile(r'\d+: (?P<interface>\w+):')
        self.ip4_re = re.compile(r'\s+inet (?P<ip4>[\d\.]+)(?:/| )')
        self.ip6_re = re.compile(r'\s+inet6 (?P<ip6>[\da-f:]+)(?:/| )')
        self.ip4_init = self.py3.format_contains(self.format_interface, 'format_ip4')
        self.ip6_init = self.py3.format_contains(self.format_interface, 'format_ip6')

    def _blacklist(self, string, blacklist):
        for ignore in blacklist:
            if fnmatch(string, ignore):
                return True
        return False

    def _get_ip_data(self):
        ip_data = self.py3.command_output(['ip', 'address', 'show'])

        new_data = {}
        for line in ip_data.splitlines():
            interface = self.interface_re.match(line)
            if interface:
                cur_interface = interface.group('interface')
                new_data[cur_interface] = {}
                continue

            ip4 = self.ip4_re.match(line)
            if ip4:
                new_data.setdefault(cur_interface, {}).setdefault(
                    'ip4', []).append(ip4.group('ip4'))
                continue

            ip6 = self.ip6_re.match(line)
            if ip6:
                new_data.setdefault(cur_interface, {}).setdefault(
                    'ip6', []).append(ip6.group('ip6'))
                continue

        return new_data

    def net_iplist(self):
        count = 0
        interface_list = []
        ip_data = self._get_ip_data()

        for interface, ips in ip_data.items():
            count_interface = 0
            if self._blacklist(interface, self.interface_blacklist):
                continue
            is_connected = False

            format_ip4 = None
            if self.ip4_init:
                ip4_list = []
                for ip4 in ips.get('ip4', []):
                    if not self._blacklist(ip4, self.ip_blacklist):
                        ip4_list.append(self.py3.safe_format(
                            self.format_ip4, {'ip4': ip4}))
                        is_connected = True
                        count_interface += 1

                ip4_separator = self.py3.safe_format(self.format_ip4_separator)
                format_ip4 = self.py3.composite_join(ip4_separator, ip4_list)

            format_ip6 = None
            if self.ip6_init:
                ip6_list = []
                for ip6 in ips.get('ip6', []):
                    if not self._blacklist(ip6, self.ip_blacklist):
                        ip6_list.append(self.py3.safe_format(
                            self.format_ip6, {'ip6': ip6}))
                        is_connected = True
                        count_interface += 1

                ip6_separator = self.py3.safe_format(self.format_ip6_separator)
                format_ip6 = self.py3.composite_join(ip6_separator, ip6_list)

            if is_connected:
                count += 1

            if self.thresholds:
                self.py3.threshold_get_color(count_interface, 'count_interface')

            interface_list.append(self.py3.safe_format(
                self.format_interface, {
                    'interface': interface,
                    'format_ip4': format_ip4,
                    'format_ip6': format_ip6,
                    'is_connected': is_connected,
                }))

        if self.thresholds:
            self.py3.threshold_get_color(count, 'count')
        interface_separator = self.py3.safe_format(self.format_interface_separator)
        format_interface = self.py3.composite_join(interface_separator, interface_list)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {'format_interface': format_interface, 'count': count})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
