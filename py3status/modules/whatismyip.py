# -*- coding: utf-8 -*-
"""
Display your public/external IP address and toggle to online status on click.

Configuration parameters:
    - cache_timeout : how often we refresh this module in seconds (default 30s)
    - format_offline : what to display when offline (default '■')
    - format_online : what to display when online placeholder are {ip} and {country}
      (default '{ip}, {country}')
    - hide_when_offline: hide the module output when offline (default False)
    - mode: default mode to display is 'text' or 'icon' (default 'icon', toggle with left click)
    - negative_cache_timeout: how often to check again when offline
    - timeout : how long before deciding we're offline
    - url: change IP check url (must output a plain text IP address)

@author ultrabug
"""
from time import time
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
    format = '{ip}, {country}'
    format_offline = '■'
    format_online = '●'
    hide_when_offline = False
    mode = 'icon'
    negative_cache_timeout = 2
    timeout = 5
    url = 'http://ip-api.com/csv'

    def on_click(self, i3s_output_list, i3s_config, event):
        """
       Toggle between display modes 'ip', 'icon' and 'country'
        """
        if self.mode == 'text':
            self.mode = 'icon'
        else:
            self.mode = 'text'

    def _get_my_ip(self):
        """
        """
        try:
            raw = urlopen(self.url, timeout=self.timeout).read()
            raw = raw.decode('utf-8').split(",")
            ip = raw[-1]
            country = raw[1]
        except Exception:
            ip = None
            country = None
        return ip, country

    def whatismyip(self, i3s_output_list, i3s_config):
        """
        """
        ip, country = self._get_my_ip()
        response = {'cached_until': time() + self.negative_cache_timeout}

        if ip is None and self.hide_when_offline:
            response['full_text'] = ''
        elif ip is not None:
            response['cached_until'] = time() + self.cache_timeout
            if self.mode == 'text':
                response['full_text'] = self.format.format(ip=ip, country=country)
                response['color'] = i3s_config['color_good']
            else:
                response['full_text'] = self.format_online
                response['color'] = i3s_config['color_good']
        else:
            response['full_text'] = self.format_offline
            response['color'] = i3s_config['color_bad']
        return response


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.whatismyip([], config))
        sleep(1)
