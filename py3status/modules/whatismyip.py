# -*- coding: utf-8 -*-
"""
Display public IP address and online status.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 30)
    format: available placeholders are {ip} and {country},
            as well as any other key in JSON fetched from `url_geo`
            (default '{ip}')
    format_offline: what to display when offline (default '■')
    format_online: what to display when online (default '●')
    hide_when_offline: hide the module output when offline (default False)
    mode: default mode to display is 'ip' or 'status' (click to toggle)
        (default 'ip')
    negative_cache_timeout: how often to check again when offline (default 2)
    timeout: how long before deciding we're offline (default 5)
    url_geo: IP to check for geo location (must output json)
        (default 'https://freegeoip.net/json')

Format placeholders:
    {country} display the country
    {ip} display current ip address
    any other key in JSON fetched from `url_geo`

Color options:
    color_bad: Offline
    color_good: Online

@author ultrabug
"""

import json
try:
    # python3
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

URL_GEO_OLD_DEFAULT = 'http://ip-api.com/json'
URL_GEO_NEW_DEFAULT = 'https://freegeoip.net/json'


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
    url_geo = URL_GEO_NEW_DEFAULT

    class Meta:
        deprecated = {
            'remove': [
                {
                    'param': 'url',
                    'msg': 'obsolete parameter, use `url_geo` instead',
                },
            ],
        }

    def post_config_hook(self):
        # Backwards compatibility
        if self.url_geo == URL_GEO_NEW_DEFAULT:
            self.format = self.format.replace('{country}', '{country_name}')
        elif self.url_geo == URL_GEO_OLD_DEFAULT:
            self.format = self.format.replace('{ip}', '{query}')

    def on_click(self, event):
        """
        Toggle between display modes 'ip' and 'status'
        """
        if self.mode == 'ip':
            self.mode = 'status'
        else:
            self.mode = 'ip'

    def _get_my_ip_info(self):
        """
        """
        try:
            resp = urlopen(self.url_geo, timeout=self.timeout).read()
            resp = json.loads(resp)
            info = {}
            for placeholder in self.py3.get_placeholders_list(self.format):
                if placeholder in resp:
                    info[placeholder] = resp[placeholder]
            return info
        except Exception:
            return None

    def whatismyip(self):
        """
        """
        info = self._get_my_ip_info()
        response = {
            'cached_until': self.py3.time_in(self.negative_cache_timeout)
        }

        if info is None and self.hide_when_offline:
            response['full_text'] = ''
        elif info is not None:
            response['cached_until'] = self.py3.time_in(self.cache_timeout)
            if self.mode == 'ip':
                response['full_text'] = self.py3.safe_format(self.format, info)
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
