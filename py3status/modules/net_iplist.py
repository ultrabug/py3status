# -*- coding: utf-8 -*-
"""
Display the list of current IPs.

This can exclude specified IPs and displays "no connection" if there are no IPs
to display.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds.
        (default 30)
    format: format of the output.
        (default 'Network: {format_iface}')
    format_iface: format string for the list of IPs of each interface.
        (default '{iface}: v4{{{ip}}} v6{{{ip6}}}')
    format_no_ip: string to show if there are no IPs to display.
        (default 'no connection')
    iface_blacklist: list of interfaces to ignore. Accepts shell-style wildcards.
        (default ['lo'])
    iface_sep: string to write between interfaces.
        (default ' ')
    ip_blacklist: list of IPs to ignore. Accepts shell-style wildcards.
        (default [])
    ip_sep: string to write between IP addresses.
        (default ',')

Format placeholders:
    {format_iface} the format_iface string.

Format placeholders for format_iface:
    {iface} name of the interface.
    {ip} list of IPv4 of the interface.
    {ip6} list of IPv6 of the interface.

Color options:
    color_bad: no IPs to show
    color_good: IPs to show

Example:

```
net_iplist {
    iface_blacklist = []
    ip_blacklist = ['127.*', '::1']
}
```

Requires:
    ip: utility found in iproute2 package
"""


import re
from subprocess import check_output
from fnmatch import fnmatch


class Py3status:
    cache_timeout = 30
    format = 'Network: {format_iface}'
    format_iface = '{iface}: v4{{{ip}}} v6{{{ip6}}}'
    iface_blacklist = ['lo']
    iface_sep = ' '
    ip_blacklist = []
    ip_sep = ','
    format_no_ip = 'no connection'

    def ip_list(self):
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': ''
        }

        connection = False
        data = self._get_data()
        iface_list = []
        for iface, ips in data.items():
            if not self._check_blacklist(iface, self.iface_blacklist):
                continue

            ip_list = []
            ip6_list = []
            for ip in ips.get('ip', []):
                if self._check_blacklist(ip, self.ip_blacklist):
                    connection = True
                    ip_list.append(ip)
            for ip6 in ips.get('ip6', []):
                if self._check_blacklist(ip6, self.ip_blacklist):
                    connection = True
                    ip6_list.append(ip6)
            iface_list.append(self.py3.safe_format(self.format_iface,
                                                   {'iface': iface,
                                                    'ip': self.ip_sep.join(ip_list),
                                                    'ip6': self.ip_sep.join(ip6_list)}))
        if not connection:
            response['full_text'] = self.py3.safe_format(self.format_no_ip,
                                                         {'format_iface':
                                                             self.iface_sep.join(iface_list)})
            response['color'] = self.py3.COLOR_BAD
        else:
            response['full_text'] = self.py3.safe_format(self.format,
                                                         {'format_iface':
                                                             self.iface_sep.join(iface_list)})
            response['color'] = self.py3.COLOR_GOOD

        return response

    def _get_data(self):
        iface_re = re.compile(r'\d+: (\w+):')
        ip_re = re.compile(r'\s+inet (\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})/')
        ip6_re = re.compile(r'\s+inet6 ([\da-f:]+)/')

        txt = check_output(['ip', 'address', 'show']).decode('utf-8').splitlines()
        len_txt = len(txt)

        idx = 0
        data = {}
        while idx < len_txt:
            iface = iface_re.match(txt[idx])
            idx += 1

            if iface is None:
                continue

            iface = iface.groups()[0]
            iface_data = data.setdefault(iface, {})
            while idx < len_txt and not iface_re.match(txt[idx]):
                ip = ip_re.match(txt[idx])
                if ip:
                    iface_data.setdefault('ip', []).append(ip.groups()[0])
                    idx += 1
                    continue
                ip6 = ip6_re.match(txt[idx])
                if ip6:
                    iface_data.setdefault('ip6', []).append(ip6.groups()[0])
                    idx += 1
                    continue
                idx += 1

        to_del = set()
        for iface, ips in data.items():
            if ips == {}:
                to_del.add(iface)
        for iface in to_del:
            del data[iface]

        return data

    def _check_blacklist(self, string, blacklist):
        for ignore in blacklist:
            if fnmatch(string, ignore):
                return False
        return True


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
