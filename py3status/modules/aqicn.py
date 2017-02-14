# -*- coding: utf-8 -*-
"""
Air quality plugin

Plugin show data fetched form aqicn.org public API

Configuration parameters:
    cache_timeout: timeout for refresh data from api (default 900)
    city: city or id of city
        for search for Your city use curl, for example (sarching for stations in Kraków):
        `curl http://api.waqi.info/search/?token=YOUR_TOKEN&keyword=kraków`
        best option is choice uid instead city name: city = '@8691'
        (default 'shanghai')
    format: format string used for text in bar (default 'aqicn: {aqicn}')
    good: (default 'Good')
    hazardous: (default 'Hazardous')
    moderate: (default 'Moderate')
    token: token from http://aqicn.org (default 'demo')
    unhealty: (default 'Unhealty')
    unhealty_sensitive: (default 'Kinda Unhealty')
    unknown: (default 'Unknown')
    very_unhealty: (default 'Very Unhealthy')

Format placeholders:
    {aqicn} air quality (text, configurable by options)
    {aqi} air quality
    {pm25} paramers from `iaqi` array

Color options:
    color_good: for good aqi
    color_hazardous: for hazardous aqi
    color_moderate: for moderate aqi
    color_unhealty: for unhealty aqi
    color_unhealty_sensitive: for unhealty for sensitive persons aqi
    color_unknown: for unknow
    color_very_unhealty: for very uhealty

Example:

```
aqicn {
    token = 'demo'
    city = 'shanghai'

    format = 'shanghai: {aqicn}'

    color_good = '#009966'
    color_hazardous = '#7E0023'
    color_moderate = '#FFDE33'
    color_unhealty = '#CC0033'
    color_unhealty_sensitive = '#FF9933'
    color_unknown = '#FFFFFF'
    color_very_unhealty = '#660099'
}
```

@author beetleman
@license BSD
"""

try:
    # python 3
    from urllib.error import URLError
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode
    from urllib2 import URLError
    from urllib2 import urlopen, Request

import json


AQI = (
    (0, 50, 'good'),
    (51, 100, 'moderate'),
    (101, 150, 'unhealty_sensitive'),
    (151, 200, 'unhealty'),
    (201, 300, 'very_unhealty'),
    (300, None, 'hazardous')
)


BASE_URL = 'http://api.waqi.info'


def get_in(coll, path, default=None):
    first = path[0]
    rest = path[1:len(path)]
    if len(path) == 1:
        return coll.get(first, default)
    return get_in(coll.get(first, default), rest, default)


class Py3status:
    cache_timeout = 900
    city = 'shanghai'

    format = 'aqicn: {aqicn}'
    good = 'Good'
    hazardous = 'Hazardous'
    moderate = 'Moderate'
    token = 'demo'
    unhealty = 'Unhealty'
    unhealty_sensitive = 'Kinda Unhealty'
    unknown = 'Unknown'
    very_unhealty = 'Very Unhealthy'

    def _call_api(self):
        kwargs = {
            'token': self.token
        }
        url_part = 'feed/{}'.format(self.city)

        url = '{base_url}/{url_part}/?{query}'.format(
            base_url=BASE_URL,
            url_part=url_part,
            query=urlencode(kwargs)
        )

        req = Request(url)
        try:
            resp = urlopen(req)
            return json.loads(resp.read().decode('utf8'))
        except URLError:
            return {}

    def _key(self, data):
        if data.get('status') == 'ok':
            aqi = get_in(data, ['data', 'aqi'], -1)

            for start, end, key in AQI:
                if aqi >= start and aqi <= end:
                    return key

        return 'unknown'

    def _full_text(self, data):
        key = self._key(data)
        aqicn = getattr(self, key, self.unknown)
        iaqi = get_in(data, ['data', 'iaqi'], {})
        aqi = get_in(data, ['data', 'aqi'])
        return self.format.format(
            aqicn=aqicn,
            aqi=aqi,
            **{k: _v.get('v') for k, _v in iaqi.items()}
        )

    def _color(self, data):
        key = self._key(data)
        color_key_default = 'color_{}'.format(key)
        color_key = color_key_default.upper()
        return getattr(
            self.py3, color_key
        )

    def aqicn(self):
        data = self._call_api()

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self._full_text(data),
            'color': self._color(data)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
