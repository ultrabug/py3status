# -*- coding: utf-8 -*-
"""
Query http://ip-api.com and display information returned. ip-api will ban your
ip address if you make over 150 requests per minute. If your IP was banned,
go here: http://ip-api.com/docs/unban

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 60)
    format_fail: format for when a query status fails
        (default '{message}')
    format_success: format for when a query status is successful
        (default '{city}, {region} {zip_code}')
    lang: language returned, choices are {en,de,es,pt-BR,fr,ja,zh-CN,ru}
        (default 'en')
    negative_cache_timeout: how often to refresh if failed or network error (default 10)
    timeout: how long before query times out (default 5)

Format placeholders:
    {as_name} display AS number and name, separated by space
    {city} display city
    {country} display country
    {country_code} display country code
    {isp} display ISP name
    {lat} display latitude
    {lon} display longitude
    {message} display error message
    {org} display Organization name
    {proxy} display proxy status
    {query} display IP used for query
    {region} display region/state short
    {region_name} display region/state
    {reverse} display Reverse DNS of the IP
    {status} display query status
    {timezone} display city timezone
    {zip_code} display zip code

Color options:
    color_bad: Offline
    color_good: Online

@author vicyap
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
    cache_timeout = 60
    format_fail = '{message}'
    format_success = '{city}, {region} {zip_code}'
    lang = 'en'
    negative_cache_timeout = 10
    timeout = 5


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
            'query': 8192,
            'status': 16384,
            'message': 32768,
            'proxy': 131072}

        fields = 0
        for name in fieldvalues:
            if self.py3.format_contains(self.format_success, name):
                fields += fieldvalues[name]
        if not self.py3.format_contains(self.format_success, 'status'):
            fields += fieldvalues['status']  # always include status
        return fields


    def _query_ip_api(self):
        """
        """
        fields = self._fields_generator()
        try:
            url = 'http://ip-api.com/json/?fields={}&?lang={}'.format(fields, self.lang)
            resp = urlopen(url, timeout=self.timeout).read()
            resp = json.loads(resp)
            status = resp.get('status', None)
        except Exception:
            resp = None
            status = None
        return resp, status

    def ip_api(self):
        """
        """
        response = {
            'cached_until': self.py3.time_in(self.negative_cache_timeout),
            'color': self.py3.COLOR_BAD
        }

        resp, status = self._query_ip_api()

        if status is None:
            response['full_text'] = 'network error'
        else:
            query = resp.get('query', '')
            if status == "success":
                response['cached_until'] = self.py3.time_in(self.cache_timeout)
                response['color'] = self.py3.COLOR_GOOD
                response['full_text'] = self.py3.safe_format(self.format_success, {
                    'as_name': resp.get('as', ''),
                    'city': resp.get('city', ''),
                    'country': resp.get('country', ''),
                    'country_code': resp.get('countryCode', ''),
                    'isp': resp.get('isp', ''),
                    'lat': resp.get('lat', ''),
                    'lon': resp.get('lon', ''),
                    'org': resp.get('org', ''),
                    'proxy': str(resp.get('proxy', False)),
                    'query': query,
                    'region': resp.get('region', ''),
                    'region_name': resp.get('regionName', ''),
                    'reverse': resp.get('reverse', ''),
                    'status': status,
                    'timezone': resp.get('timezone', ''),
                    'zip_code': resp.get('zip', '')})
            elif status == "fail":
                response['full_text'] = self.py3.safe_format(self.format_fail, {
                    'message': resp.get('message', ''),
                    'status': status,
                    'query': query
                    })
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
