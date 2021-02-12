"""
Display list of network interfaces and IP addresses.

This module supports both IPv4 and IPv6. There is the possibility to blacklist
interfaces and IPs, as well as to show interfaces with no IP address. It will
show an alternate text if no IP are available.

Configuration parameters:
    cache_timeout: refresh interval for this module in seconds.
        (default 30)
    format: format of the output.
        (default 'Network: {format_iface}')
    format_iface: format string for the list of IPs of each interface.
        (default '{iface}:[ {ip4}][ {ip6}]')
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
    remove_empty: do not show interfaces with no IP.
        (default True)

Format placeholders:
    {format_iface} the format_iface string.

Format placeholders for format_iface:
    {iface} name of the interface.
    {ip4} list of IPv4 of the interface.
    {ip6} list of IPv6 of the interface.

Color options:
    color_bad: no IPs to show
    color_good: IPs to show

Requires:
    ip: utility found in iproute2 package

Examples:
```
net_iplist {
    iface_blacklist = []
    ip_blacklist = ['127.*', '::1']
}
```

@author guiniol

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
    format = "Network: {format_iface}"
    format_iface = "{iface}:[ {ip4}][ {ip6}]"
    format_no_ip = "no connection"
    iface_blacklist = ["lo"]
    iface_sep = " "
    ip_blacklist = []
    ip_sep = ","
    remove_empty = True

    def post_config_hook(self):
        self.iface_re = re.compile(r"\d+: (?P<iface>[\w\-]+):")
        self.ip_re = re.compile(r"\s+inet (?P<ip4>[\d.]+)(?:/| )")
        self.ip6_re = re.compile(
            r"\s+inet6 (?P<ip6>[\da-f:]+)(?:/\d{1,3}| ) scope global dynamic"
        )

    def net_iplist(self):
        response = {
            "cached_until": self.py3.time_in(seconds=self.cache_timeout),
            "full_text": "",
        }

        connection = False
        data = self._get_data()
        iface_list = []
        for iface, ips in data.items():
            if not self._check_blacklist(iface, self.iface_blacklist):
                continue

            ip4_list = []
            ip6_list = []
            for ip4 in ips.get("ip4", []):
                if self._check_blacklist(ip4, self.ip_blacklist):
                    connection = True
                    ip4_list.append(ip4)
            for ip6 in ips.get("ip6", []):
                if self._check_blacklist(ip6, self.ip_blacklist):
                    connection = True
                    ip6_list.append(ip6)
            iface_list.append(
                self.py3.safe_format(
                    self.format_iface,
                    {
                        "iface": iface,
                        "ip4": self.ip_sep.join(ip4_list),
                        "ip6": self.ip_sep.join(ip6_list),
                    },
                )
            )
        if not connection:
            response["full_text"] = self.py3.safe_format(
                self.format_no_ip,
                {"format_iface": self.py3.composite_join(self.iface_sep, iface_list)},
            )
            response["color"] = self.py3.COLOR_BAD
        else:
            response["full_text"] = self.py3.safe_format(
                self.format,
                {"format_iface": self.py3.composite_join(self.iface_sep, iface_list)},
            )
            response["color"] = self.py3.COLOR_GOOD

        return response

    def _get_data(self):
        txt = self.py3.command_output(["ip", "address", "show"]).splitlines()

        data = {}
        for line in txt:
            iface = self.iface_re.match(line)
            if iface:
                cur_iface = iface.group("iface")
                if not self.remove_empty:
                    data[cur_iface] = {}
                continue

            ip4 = self.ip_re.match(line)
            if ip4:
                data.setdefault(cur_iface, {}).setdefault("ip4", []).append(
                    ip4.group("ip4")
                )
                continue

            ip6 = self.ip6_re.match(line)
            if ip6:
                data.setdefault(cur_iface, {}).setdefault("ip6", []).append(
                    ip6.group("ip6")
                )
                continue

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
