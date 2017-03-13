# -*- coding: utf-8 -*-
"""
Display air quality polluting in a given location.

An air quality index (AQI) is a number used by government agencies to communicate
to the public how polluted the air currently is or how polluted it is forecast to
become. As the AQI increases, an increasingly large percentage of the population
is likely to experience increasingly severe adverse health effects. Different
countries have their own air quality indices, corresponding to different national
air quality standards.

Configuration parameters:
    auth_token: Required. Personal token. http://aqicn.org (default 'demo')
    cache_timeout: refresh interval for this module. A message from the site:
        The default quota is max 1000 (one thousand) requests per minute (~16RPS)
        and with burst up to 60 requests. Read more: http://aqicn.org/api/
        (default 3600)
    format: display format for this module (default 'AQI: {aqi} {category}')
    location: location/uid to query. To search for nearby stations in Kraków,
        use `curl http://api.waqi.info/search/?token=YOUR_TOKEN&keyword=kraków`
        We recommend you to use uid instead of name in location, eg "@8691"
        (default 'Shanghai')

Format placeholders:
    {aqi} air quality index
    {category} health risk category
    {location} location/uid
    {something} output from "something" parameter in `iaqi` array.

__Note: To explain more about {something} parameter, the station may have
their own set of custom parameters such as {pm25}, {pm10}, etc. You can find
out by using curl command above and look for them.__

Category options:
    category_<name>: display name
        eg category_very_unhealthy = 'Level 5: Wear your mask'

Color options:
    color_<category>: display color
        eg color_hazardous = '#7E0023'

Example:
```
air_quality {
    auth_token = 'demo'
    location = 'Shanghai'
    format = 'Shanghai: {aqi} {category}'
}
```
@author beetleman
@license BSD
"""

try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

AQI = (
    (0, 50, 'good'),
    (51, 100, 'moderate'),
    (101, 150, 'unhealthy_sensitive'),
    (151, 200, 'unhealthy'),
    (201, 300, 'very_unhealthy'),
    (301, int('inf'), 'hazardous')
)
CATEGORY = {
    'good': 'Good',
    'hazardous': 'Hazardous',
    'moderate': 'Moderate',
    'unhealthy': 'Unhealthy',
    'unhealthy_sensitive': 'Unhealthy for Sensitive Groups',
    'unknown': 'Unknown',
    'very_unhealthy': 'Very Unhealthy',
}
COLOR = {
    'good': '#009966',
    'hazardous': '#7E0023',
    'moderate': '#FFDE33',
    'unhealthy': '#CC0033',
    'unhealthy_sensitive': '#FF9933',
    'unknown': '#ffffff',
    'very_unhealthy': '#660099',
}
STRING_UNKNOWN = 'Unknown'
URL = 'http://api.waqi.info'


def _get_in(coll, path, default=None):
    first = path[0]
    rest = path[1:len(path)]
    if len(path) == 1:
        return coll.get(first, default)
    return _get_in(coll.get(first, default), rest, default)


class Py3status:
    auth_token = 'demo'
    cache_timeout = 3600
    format = 'AQI: {aqi} {category}'
    location = 'Shanghai'

    def _update_aqi(self):
        url_path = 'feed/{}'.format(self.location)
        url_token = {'token': self.auth_token}
        url_full = '{url_base}/{url_path}/?{url_query}'.format(
            url_base=URL,
            url_path=url_path,
            url_query=urlencode(url_token)
        )
        try:
            self._api_data = self.py3.request(url_full).json()
        except (self.py3.RequestException):
            self._api_data = None

    def _update_key(self):
        if self._api_data.get('status') == 'ok':
            aqi = _get_in(self._api_data, ['data', 'aqi'], -1)
            if type(aqi) is not int:
                self._key = 'unknown'
                return
            for start, end, key in AQI:
                if aqi >= start and aqi <= end:
                    self._key = key
                    return
        self._key = 'unknown'

    def _get_full_text(self):
        aqi = _get_in(self._api_data, ['data', 'aqi'])
        iaqi = _get_in(self._api_data, ['data', 'iaqi'], {})
        try:
            category = getattr(self, 'CATEGORY_{}'.format(self._key).lower())
        except:
            category = CATEGORY.get(self._key)
        if not category:
            category = STRING_UNKNOWN
        return self.format.format(
            location=self.location,
            category=category,
            aqi=aqi,
            **{k: _v.get('v') for k, _v in iaqi.items()}
        )

    def _get_color(self):
        color = getattr(self.py3, 'COLOR_{}'.format(self._key.upper()))
        if not color:
            color = COLOR.get(self._key)
        if not color:
            color = None
        return color

    def air_quality(self):
        self._update_aqi()
        self._update_key()

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self._get_full_text(),
            'color': self._get_color()
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
