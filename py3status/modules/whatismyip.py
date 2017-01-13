# -*- coding: utf-8 -*-
"""
Display your public/external IP address and toggle to online status on click.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 30s)
    format: available placeholders are {ip} and {country} (default '{ip}')
            If {country} is used the data is queried from
            "http://ip-api.com/csv"
            instead of
            "http://ultrabug.fr/py3status/whatismyip".
    format_offline: what to display when offline (default '■')
    format_online: what to display when online (default '●')
    hide_when_offline: hide the module output when offline (default False)
    mode: default mode to display is 'ip' or 'status' (click to toggle)
        (default 'ip')
    negative_cache_timeout: how often to check again when offline (default 2)
    timeout: how long before deciding we're offline (default 5)
    url: change IP check url (must output a plain text IP address)
        (default 'http://ultrabug.fr/py3status/whatismyip')


Format placeholders:
    {ip} display current ip address
    {country} display the country

Color options:
    color_bad: Offline
    color_good: Online

@author ultrabug
"""

try:
    # python3
    from urllib.request import urlopen
except:
    from urllib2 import urlopen


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 30
    format = '{ip}'
    format_offline = u'■'
    format_online = u'●'
    hide_when_offline = False
    mode = 'ip'
    negative_cache_timeout = 2
    timeout = 5
    url = 'http://ultrabug.fr/py3status/whatismyip'
    url_geo = 'http://ip-api.com/csv'

    def on_click(self, event):
        """
        Toggle between display modes 'ip' and 'status'
        """
        if self.mode == 'ip':
            self.mode = 'status'
        else:
            self.mode = 'ip'

    def _get_my_ip(self):
        """
        """
        country = ""
        try:
            if '{country}' in self.format:
                self.url = self.url_geo
            ip = urlopen(self.url, timeout=self.timeout).read()
            ip = ip.decode('utf-8')
            if '{country}' in self.format:
                ip = ip.split(",")
                ip, country = ip[-1], ip[1]
        except Exception:
            ip = None
        return ip, country

    def whatismyip(self):
        """
        """
        ip, country = self._get_my_ip()
        response = {
            'cached_until': self.py3.time_in(self.negative_cache_timeout)
        }

        if ip is None and self.hide_when_offline:
            response['full_text'] = ''
        elif ip is not None:
            response['cached_until'] = self.py3.time_in(self.cache_timeout)
            if self.mode == 'ip':
                response['full_text'] = self.py3.safe_format(self.format, {
                    'ip': ip,
                    'country': country})
            else:
                response['full_text'] = self.format_online
                response['color'] = self.py3.COLOR_GOOD
        else:
            response['full_text'] = self.format_offline
            response['color'] = self.py3.COLOR_BAD
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
