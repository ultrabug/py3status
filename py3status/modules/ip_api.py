# -*- coding: utf-8 -*-
"""
Display your public/external IP address and toggle to online status on click.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 30)
    format: available placeholders are {ip} and {country}
            (default '{country}')
    negative_cache_timeout: how often to check again when offline (default 2)
    timeout: how long before deciding we're offline (default 5)
    url: IP to check for geo location (must output json)
        (default 'http://ip-api.com/json')

Format placeholders:
    {country} display the country
    {country_code} display country code
    {region} display region
    {region_name} display region name
    {city} display city
    {zip_code} display zip code
    {lat} display latitude
    {lon} display longitude


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
    cache_timeout = 30
    format = '{country}'
    negative_cache_timeout = 2
    timeout = 5
    url = 'http://ip-api.com/json'
    country = None
    country_code = None
    region = None
    region_name = None
    city = None
    zip_code = None
    lat = None
    lon = None

    def on_click(self, event):
        """
        Toggle between display modes
        """
        if self.mode == 'ip':
            self.mode = 'status'
        else:
            self.mode = 'ip'

    def _get_my_location(self):
        """
        """
        try:
            resp = urlopen(self.url, timeout=self.timeout).read()
            resp = json.loads(resp)
            status = resp['status']
            self.country = resp['country']
            self.country_code = resp['countryCode']
            self.region = resp['region']
            self.region_name = resp['regionName']
            self.city = resp['city']
            self.zip_code = resp['zip']
            self.lat = resp['lat']
            self.lon = resp['lon']
        except Exception:
            self.status = False
        return status == "success"

    def ip_api(self):
        """
        """
        status = self._get_my_location()
        response = {
            'cached_until': self.py3.time_in(self.negative_cache_timeout)
        }

        if status:
            response['cached_until'] = self.py3.time_in(self.cache_timeout)
            response['full_text'] = self.py3.safe_format(self.format, {
                'country': self.country,
                'country_code': self.country_code,
                'region': self.region,
                'region_name': self.region_name,
                'city': self.city,
                'zip_code': self.zip_code,
                'lat': self.lat,
                'lon': self.lon})
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
            'format': '{country}, {country_code}, {region}, {region_name}, {city}, {zip_code}, {lat}, {lon}'
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
