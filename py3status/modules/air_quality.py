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
    format: display format for this module (default '{location}: {aqi} {category}')
    location: location or uid to query. To search for nearby stations in Kraków,
        use `curl http://api.waqi.info/search/?token=YOUR_TOKEN&keyword=kraków`
        We recommend you to use uid instead of name in location, eg "@8691"
        (default 'Shanghai')

Format placeholders:
    {aqi} air quality index
    {category} health risk category
    {location} location or uid

Note: Stations may use {pm25}, {pm10}, {o3}, {so2}, or other parameters.
See http://api.waqi.info/feed/@UID/?token=TOKEN (Replace UID and TOKEN)

Category options:
    category_<name>: display name
        eg category_very_unhealthy = 'Level 5: Wear a mask'

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
@author beetleman, lasers
@license BSD

SAMPLE OUTPUT
{'color':'#009966', 'full_text':'Shanghai: 49 Good'}

aqi_moderate
{'color':'#FFDE33', 'full_text':'Shanghai: 65 Moderate'}

aqi_sensitively_unhealthy
{'color':'#FF9933', 'full_text':'Shanghai: 103 Sensitively Unhealthy'}

aqi_unhealthy
{'color':'#CC0033', 'full_text':'Shanghai: 165 Unhealthy'}

aqi_very_unhealthy
{'color':'#660099', 'full_text':'Shanghai: 220 Very Unhealthy'}

aqi_hazardous
{'color':'#7E0023', 'full_text':'Shanghai: 301 Hazardous'}
"""

AQI = (
    (0, 50, 'good'),
    (51, 100, 'moderate'),
    (101, 150, 'sensitively_unhealthy'),
    (151, 200, 'unhealthy'),
    (201, 300, 'very_unhealthy'),
    (301, float('inf'), 'hazardous')
)
CATEGORY = {
    'good': 'Good',
    'hazardous': 'Hazardous',
    'moderate': 'Moderate',
    'sensitively_unhealthy': 'Sensitively Unhealthy',
    'unhealthy': 'Unhealthy',
    'unknown': 'Unknown',
    'very_unhealthy': 'Very Unhealthy',
}
COLOR = {
    'good': '#009966',
    'hazardous': '#7E0023',
    'moderate': '#FFDE33',
    'sensitively_unhealthy': '#FF9933',
    'unhealthy': '#CC0033',
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
    """
    """
    # available configuration parameters
    auth_token = 'demo'
    cache_timeout = 3600
    format = '{location}: {aqi} {category}'
    location = 'Shanghai'

    def post_config_hook(self):
        url_path = 'feed/{}'.format(self.location)
        self.url_token = {'token': self.auth_token}
        self.url_full = '{url_base}/{url_path}/'.format(
            url_base=URL,
            url_path=url_path
        )

    def _update_data(self):
        try:
            self._api_data = self.py3.request(self.url_full, params=self.url_token).json()
        except (self.py3.RequestException):
            self._api_data = {}

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
        aqi = _get_in(self._api_data, ['data', 'aqi'], {})
        iaqi = _get_in(self._api_data, ['data', 'iaqi'], {})
        city = _get_in(self._api_data, ['data', 'city'], {})
        try:
            category = getattr(self, 'CATEGORY_{}'.format(self._key).lower())
        except:
            category = CATEGORY.get(self._key)
        if not category:
            category = STRING_UNKNOWN
        return self.py3.safe_format(self.format,
                                    dict(location=city.get('name'),
                                         category=category,
                                         aqi=aqi,
                                         **{k: v.get('v') for k, v in iaqi.items()}))

    def _get_color(self):
        color = getattr(self.py3, 'COLOR_{}'.format(self._key.upper()))
        if not color:
            color = COLOR.get(self._key)
        return color

    def air_quality(self):
        self._update_data()
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
