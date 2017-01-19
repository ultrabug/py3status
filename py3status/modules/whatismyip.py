# -*- coding: utf-8 -*-
"""
Display your public/external IP address and toggle to online status on click.
Additionally display information about your external IP address

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 30)
    format: available placeholders are listed below
            (default '{ip}')
    format_offline: what to display when offline (default '■')
    format_online: what to display when online (default '●')
    hide_when_offline: hide the module output when offline (default False)
    lang: language returned, choices are {en,de,es,pt-BR,fr,ja,zh-CN,ru}
        (default 'en')
    mode: default mode to display is 'ip' or 'status' (click to toggle)
        (default 'ip')
    negative_cache_timeout: how often to check again when offline (default 2)
    timeout: how long before deciding we're offline (default 5)

Format placeholders:
    {as_name} display AS number and name, separated by space
    {city} display city
    {country} display country
    {country_code} display country code
    {ip} display IP used for query
    {isp} display ISP name
    {lat} display latitude
    {lon} display longitude
    {message} display error message
    {org} display Organization name
    {proxy} display proxy status
    {region} display region/state short
    {region_name} display region/state
    {reverse} display Reverse DNS of the IP
    {status} display query status
    {timezone} display city timezone
    {zip_code} display zip code

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


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 30
    format = u'{ip}'
    format_offline = u'■'
    format_online = u'●'
    hide_when_offline = False
    lang = 'en'
    mode = 'ip'
    negative_cache_timeout = 2
    timeout = 5

    def on_click(self, event):
        """
        Toggle between display modes 'ip' and 'status'
        """
        if self.mode == 'ip':
            self.mode = 'status'
        else:
            self.mode = 'ip'

    def _fields_generator(self):
        """
        """
        fieldvalues = {
            'country': 1,
            'country_code': 2,
            'region': 4,
            'region_name': 8,
            'city': 16,
            'zip_code': 32,
            'lat': 64,
            'lon': 128,
            'timezone': 256,
            'isp': 512,
            'org': 1024,
            'as_name': 2048,
            'reverse': 4096,
            'ip': 8192,
            'status': 16384,
            'message': 32768,
            'proxy': 131072}
        fields = 0
        for name in fieldvalues:
            if self.py3.format_contains(self.format, name):
                fields += fieldvalues[name]
        if not self.py3.format_contains(self.format, 'status'):
            fields += fieldvalues['status']  # always include status
        return fields

    def _query_ip(self):
        """
        """
        fields = self._fields_generator()
        try:
            url = 'http://ip-api.com/json/?fields={}&lang={}'.format(fields, self.lang)
            resp = urlopen(url, timeout=self.timeout).read()
            resp = json.loads(resp)
            status = resp.get('status', None)
        except Exception:
            resp = None
            status = None
        return resp, status

    def whatismyip(self):
        """
        """
        response = {
            'cached_until': self.py3.time_in(self.negative_cache_timeout),
            'color': self.py3.COLOR_BAD
        }

        resp, status = self._query_ip()

        if status is None:
            if self.hide_when_offline:
                response['full_text'] = ''
            else:
                response['full_text'] = self.format_offline
        else:
            response['cached_until'] = self.py3.time_in(self.cache_timeout)
            message = resp.get('message', '')
            if self.mode == 'ip':
                if status == "success":
                    response['color'] = self.py3.COLOR_GOOD
                    response['full_text'] = self.py3.safe_format(self.format, {
                        'as_name': resp.get('as', ''),
                        'city': resp.get('city', ''),
                        'country': resp.get('country', ''),
                        'country_code': resp.get('countryCode', ''),
                        'ip': resp.get('query', ''),
                        'isp': resp.get('isp', ''),
                        'lat': resp.get('lat', ''),
                        'lon': resp.get('lon', ''),
                        'message': message,
                        'org': resp.get('org', ''),
                        'proxy': str(resp.get('proxy', False)),
                        'region': resp.get('region', ''),
                        'region_name': resp.get('regionName', ''),
                        'reverse': resp.get('reverse', ''),
                        'status': status,
                        'timezone': resp.get('timezone', ''),
                        'zip_code': resp.get('zip', '')})
                elif status == "fail":
                    response['full_text'] = message
            elif self.mode == 'status':
                response['color'] = self.py3.COLOR_GOOD
                response['full_text'] = self.format_online
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
