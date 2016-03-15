# -*- coding: utf-8 -*-
"""
Display your public/external IP address and toggle to online status on click.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 30s)
    format: the only placeholder available is {ip} (default '{ip}')
    format_offline: what to display when offline
    format_online: what to display when online
    hide_when_offline: hide the module output when offline (default False)
    mode: default mode to display is 'ip' or 'status' (click to toggle)
    negative_cache_timeout: how often to check again when offline
    timeout: how long before deciding we're offline
    url: change IP check url (must output a plain text IP address)

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
    format = '{ip}'
    format_offline = '■'
    format_online = '●'
    hide_when_offline = False
    mode = 'ip'
    negative_cache_timeout = 2
    timeout = 5
    url = 'http://ultrabug.fr/py3status/whatismyip'

    def on_click(self, i3s_output_list, i3s_config, event):
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
        try:
            ip = urlopen(self.url, timeout=self.timeout).read()
            ip = ip.decode('utf-8')
        except Exception:
            ip = None
        return ip

    def whatismyip(self, i3s_output_list, i3s_config):
        """
        """
        ip = self._get_my_ip()
        response = {'cached_until': time() + self.negative_cache_timeout}

        if ip is None and self.hide_when_offline:
            response['full_text'] = ''
        elif ip is not None:
            response['cached_until'] = time() + self.cache_timeout
            if self.mode == 'ip':
                response['full_text'] = self.format.format(ip=ip)
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
