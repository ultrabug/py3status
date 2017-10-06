# -*- coding: utf-8 -*-
"""
Display list of network interfaces and IP addresses.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 30)
    format: display format for this module
        (default '\?color=count [{format_iface}|\?show no connection]')
    format_iface: display format for network interfaces
        (default '\?if=is_connected {iface}:[ {ip4}][ {ip6}]')
    format_iface_separator: show separator if more than one (default ' ')
    format_ip_separator: show separator if more than one (default ', ')
    iface_blacklist: specify a list of interfaces to ignore.
        accepts shell-style wildcards.
        (default ['lo'])
    ip_blacklist: specify a list of IPs to ignore.
        accepts shell-style wildcards.
        (default [])
    thresholds: specify color thresholds to use.
        (default [(0, 'bad'), (1, 'good')])

Format placeholders:
    {count} number of connections
    {format_iface} format for network interfaces

format_iface placeholders:
    {iface} interface name, eg eno1
    {ip4} interface IPv4 addresses, eg 192.168.1.103
    {ip6} interface IPv6 addresses, eg fe80::d625:7ea8:e729:716c/64
    {is_connected} a boolean based on interface data

Color thresholds:
    count: print color based on number of connections

Requires:
    iproute2: show/manipulate routing, devices, policy routing and tunnels

Examples:
```
# ask @guiniol for a description
net_iplist {
    iface_blacklist = []
    ip_blacklist = ['127.*', '::1']
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
    format = '\?color=count [{format_iface}|\?show no connection]'
    format_iface = '\?if=is_connected {iface}:[ {ip4}][ {ip6}]'
    format_iface_separator = ' '
    format_ip_separator = ', '
    iface_blacklist = ['lo']
    ip_blacklist = []
    thresholds = [(0, 'bad'), (1, 'good')]

    def post_config_hook(self):
        self.iface_re = re.compile(r'\d+: (?P<iface>\w+):')
        self.ip4_re = re.compile(r'\s+inet (?P<ip4>[\d\.]+)(?:/| )')
        self.ip6_re = re.compile(r'\s+inet6 (?P<ip6>[\da-f:]+)(?:/| )')
        self.ip4_init = self.py3.format_contains(self.format_iface, 'ip4')
        self.ip6_init = self.py3.format_contains(self.format_iface, 'ip6')

    def _blacklist(self, string, blacklist):
        for ignore in blacklist:
            if fnmatch(string, ignore):
                return True
        return False

    def _get_ip_data(self):
        ip_data = self.py3.command_output(['ip', 'address', 'show'])

        new_data = {}
        for line in ip_data.splitlines():
            iface = self.iface_re.match(line)
            if iface:
                cur_iface = iface.group('iface')
                new_data[cur_iface] = {}
                continue

            ip4 = self.ip4_re.match(line)
            if ip4:
                new_data.setdefault(cur_iface, {}).setdefault(
                    'ip4', []).append(ip4.group('ip4'))
                continue

            ip6 = self.ip6_re.match(line)
            if ip6:
                new_data.setdefault(cur_iface, {}).setdefault(
                    'ip6', []).append(ip6.group('ip6'))
                continue

        return new_data

    def net_iplist(self):
        count = 0
        iface_list = []
        ip_data = self._get_ip_data()
        ip_separator = self.py3.safe_format(self.format_ip_separator)

        for iface, ips in ip_data.items():
            if self._blacklist(iface, self.iface_blacklist):
                continue

            is_connected = False

            ip4 = None
            if self.ip4_init:
                ip4_list = []
                for ip4 in ips.get('ip4', []):
                    if not self._blacklist(ip4, self.ip_blacklist):
                        ip4_list.append(self.py3.safe_format(ip4))
                        is_connected = True

                ip4 = self.py3.composite_join(ip_separator, ip4_list)

            ip6 = None
            if self.ip6_init:
                ip6_list = []
                for ip6 in ips.get('ip6', []):
                    if not self._blacklist(ip6, self.ip_blacklist):
                        ip6_list.append(self.py3.safe_format(ip6))
                        is_connected = True

                ip6 = self.py3.composite_join(ip_separator, ip6_list)

            if is_connected:
                count += 1

            iface_list.append(self.py3.safe_format(
                self.format_iface, {
                    'iface': iface,
                    'ip4': ip4,
                    'ip6': ip6,
                    'is_connected': is_connected,
                }))

        self.py3.threshold_get_color(count, 'count')
        iface_separator = self.py3.safe_format(self.format_iface_separator)
        format_iface = self.py3.composite_join(iface_separator, iface_list)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {'format_iface': format_iface, 'count': count})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
