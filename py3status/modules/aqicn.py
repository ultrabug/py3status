# -*- coding: utf-8 -*-
"""
# TODO: fill this docstring
Single line summary

Longer description of the module.  This should help users understand the
modules purpose.

Configuration parameters:
    parameter: Explanation of this parameter (default <value>)
    parameter_other: This parameter has a longer explanation that continues
        onto a second line so it is indented.
        (default <value>)

Format placeholders:
    {info} Description of the placeholder

Color options:
    color_meaning: what this signifies, defaults to color_good
    color_meaning2: what this signifies

Requires:
    program: Information about the program
    python_lib: Information on the library

Example:

```
aqicn {
    token = 'demo'
    city = 'shanghai'
}
```

@author beetleman
@license BSD
"""
import functools

try:
    # python 3
    from urllib.error import URLError
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from utllib2 import urlencode
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
    good = 'Good'
    moderate = 'Moderate'
    unhealty_sensitive = 'Kinda Unhealty'
    unhealty = 'Unhealty'
    very_unhelty = 'Very Unhealthy'
    hazardous = 'Hazardous'
    unknown = 'Unknown'

    color_good = '#009966'
    color_moderate = '#FFDE33'
    color_unhealty_sensitive = '#FF9933'
    color_unhealty = '#CC0033'
    color_very_unhelty = '#660099'
    color_hazardous = '#7E0023'
    color_unknown = '#FFFFFF'

    token = 'demo'
    city = 'shanghai'

    cache_timeout = 900

    format = 'aqicn: {aqicn}'

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
        ) or getattr(
            self, color_key_default, self.color_unknown
        )

    def aqicn(self):
        data = self._call_api()
        key = self._key(data)

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
