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
    iface_blacklist: list of interfaces to ignore.
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
        iface_txt = ''
        for iface, ips in data.items():
            if iface in self.iface_blacklist:
                continue

            txt_ip = ''
            txt_ip6 = ''
            for ip in ips.get('ip', []):
                if self._check_blacklist(ip):
                    connection = True
                    txt_ip += ip + self.ip_sep
            txt_ip = txt_ip[:-len(self.ip_sep)]
            for ip in ips.get('ip6', []):
                if self._check_blacklist(ip):
                    connection = True
                    txt_ip6 += ip + self.ip_sep
            txt_ip6 = txt_ip6[:-len(self.ip_sep)]
            iface_txt += self.py3.safe_format(self.format_iface, {'iface': iface,
                                                                  'ip': txt_ip,
                                                                  'ip6': txt_ip6})
            iface_txt += self.iface_sep
            iface_txt = iface_txt[:-len(self.iface_sep)]
        if not connection:
            response['full_text'] = self.py3.safe_format(self.format_no_ip,
                                                         {'format_iface': iface_txt})
            response['color'] = self.py3.COLOR_BAD
        else:
            response['full_text'] = self.py3.safe_format(self.format,
                                                         {'format_iface': iface_txt})
            response['color'] = self.py3.COLOR_GOOD

        return response

    def _get_data(self):
        iface_re = re.compile(r'\d+: (\w+):')
        ip_re = re.compile(r'\s+inet (\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})/')
        ip6_re = re.compile(r'\s+inet6 ([\da-f:]+)/')

        txt = check_output(['ip', 'address', 'show']).decode('utf-8').split('\n')
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

    def _check_blacklist(self, ip):
        for ignore in self.ip_blacklist:
            if fnmatch(ip, ignore):
                return False
        return True


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
