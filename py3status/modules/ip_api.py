# -*- coding: utf-8 -*-
"""
Query http://ip-api.com and display information returned. ip-api will ban your ip address if you make over 150 requests
per minute. If your IP was banned, go here: http://ip-api.com/docs/unban

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 60)
    format: available placeholders are {ip} and {country}
            (default '{city}, {region} {zip_code}')
    lang: language returned, choices are {en,de,es,pt-BR,fr,ja,zh-CN,ru}
        (default 'en')
    negative_cache_timeout: how often to refresh if failed or timeout (default 10)
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
    format = '{city}, {region} {zip_code}'
    lang = 'en'
    negative_cache_timeout = 10
    timeout = 5


    def _fields_generator(self):
        """
        """
        fieldvalues = {
            'country': 1,
            'countryCode': 2,
            'region': 4,
            'regionName': 8,
            'city': 16,
            'zipCode': 32,
            'lat': 64,
            'lon': 128,
            'timezone': 256,
            'isp': 512,
            'org': 1024,
            'as': 2048,
            'reverse': 4096,
            'query': 8192,
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
            'cached_until': self.py3.time_in(self.negative_cache_timeout)
        }

        resp, status = self._query_ip_api()

        as_name = resp.get('as', '')
        city = resp.get('city', '')
        country = resp.get('country', '')
        country_code = resp.get('countryCode', '')
        isp = resp.get('isp', '')
        lat = resp.get('lat', 0)
        lon = resp.get('lon', 0)
        message = resp.get('message', '')
        org = resp.get('org', '')
        proxy = resp.get('proxy', True)
        query = resp.get('query', '')
        region = resp.get('region', '')
        region_name = resp.get('regionName', '')
        reverse = resp.get('reverse', '')
        status = resp.get('status', '')
        timezone = resp.get('timezone', '')
        zip_code = resp.get('zip', '')

        if status == "success":
            response['cached_until'] = self.py3.time_in(self.cache_timeout)
            response['full_text'] = self.py3.safe_format(self.format, {
                'as_name': as_name,
                'city': city,
                'country': country,
                'country_code': country_code,
                'isp': isp,
                'lat': lat,
                'lon': lon,
                'org': org,
                'proxy': str(proxy),
                'query': query,
                'region': region,
                'region_name': region_name,
                'reverse': reverse,
                'status': status,
                'timezone': timezone,
                'zip_code': zip_code})
        elif status == "fail":
            response['full_text'] = self.py3.safe_format(self.format, {
                'message': message,
                'status': status,
                'query': query
                })
        else:
            response['full_text'] = ''
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
            'format': '{as_name}, {city}, {country}, {country_code}, {isp}, {lat}, {lon}, {org}, {proxy}, {query}, {region}, {region_name}, {reverse}, {status}, {timezone}, {zip_code}'
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
