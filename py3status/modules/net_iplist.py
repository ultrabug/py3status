# -*- coding: utf-8 -*-
"""
Display list of network interfaces and IP addresses.

This module supports both IPv4 and IPv6. There is the possibility to blacklist
interfaces and IPs, as well as to show interfaces with no IP address. It will
show an alternate text if no IP are available.

Configuration parameters:
    cache_timeout: refresh interval for this module in seconds.
        (default 30)
    format: format of the output.
        (default '\?color=count [Network: {format_iface}|\?show no connection]')
    format_iface: format string for the list of IPs of each interface.
        (default '\?if=is_connected {iface}:[ {ip4}][ {ip6}]')
    format_iface_separator: show separator if more than one.
        (default ' ')
    format_ip_separator: show separator if more than one.
        (default ', ')
    iface_blacklist: list of interfaces to ignore. Accepts shell-style wildcards.
        (default ['lo'])
    ip_blacklist: list of IPs to ignore. Accepts shell-style wildcards.
        (default [])
    thresholds: specify color thresholds to use.
        (default [(0, 'bad'), (1, 'good')])

Format placeholders:
    {count} number of IPs.
    {format_iface} the format_iface string.

Format placeholders for format_iface:
    {iface} name of the interface.
    {ip4} list of IPv4 of the interface.
    {ip6} list of IPv6 of the interface.
    {is_connected} a boolean based on interface data.

Color thresholds:
    count: print color based on number of IPs

Example:
```
# ask @guiniol for a description
net_iplist {
    iface_blacklist = []
    ip_blacklist = ['127.*', '::1']
}
```

Requires:
    ip: show/manipulate routing, devices, policy routing and tunnels

@author guiniol, lasers

SAMPLE OUTPUT
{'color': '#00FF00',
 'full_text': u'Network: wls1: 192.168.1.3 fe80::f861:44bd:694a:b99c'}
"""


import re
from fnmatch import fnmatch


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 30
    format = '\?color=count [Network: {format_iface}|\?show no connection]'
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

    def ip_list(self):
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

    def _blacklist(self, string, blacklist):
        for ignore in blacklist:
            if fnmatch(string, ignore):
                return True
        return False


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
