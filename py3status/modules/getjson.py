# -*- coding: utf-8 -*-
"""
Display JSON data fetched from a URL.

This module gets the given `url` configuration parameter and assumes the
response is a JSON object. The keys of the JSON object are used as the format
placeholders. The format placeholders are replaced by the value. Objects that
are nested can be accessed by using the `delimiter` configuration parameter
in between.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 60)
    flatten_delimiter: the delimiter between the objects (default '-')
    flatten_intermediates: preserve the elements (default False)
    flatten_parent_key: add a prefix to use in a dict (default None)
    format: display format for this module (default None)
    format_json: display format for items in the list (default None)
    format_separator: show separator if more than one (default ' ')
    parent_key: specify a parent key in a dict to get (default None)
    request_auth: auth in tuple, eg ('username', 'password') (default None)
    request_cookiejar: an object of a CookieJar subclass (default None)
    request_data: specify POST data as a dict to use (default None)
    request_headers: http headers to be added as a dict (default None)
    request_params: extra query string parameters as a dict (default None)
    request_timeout: time to wait for a response, in seconds (default 10)
    request_url: specify a URL to request (default None)
    thresholds: specify color thresholds to use (default [])

Explanation:
    Placeholders will be replaced by the JSON keys.

    Placeholders for objects with sub-objects are flattened using
    `flatten_delimiter` in between, eg `{'parent': {'child': 'value'}}`
    will be converted to placeholder `{parent-child}`.

    Placeholders for list elements have `flatten_delimiter` followed by
    the index, eg `{'parent': ['item1', 'item2']` will be converted to
    placeholder `{parent-0}` for `item1` and `{parent-1}` for `item2`.

    If it is a dictionary...
        See `Explanation`

    If it is a list...
        See `Explanation`

    If it is a list...
        Format placeholders:
            {format_json} format for items

        format_json placeholders:
            {index} item number, eg 1
            See `Explanation`

Color thresholds:
    `key`: print a color based on the value of `key`

Examples (dict):
```
# straightforward key replacement
getjson {
    request_url = 'http://ip-api.com/json'
    format = '{lat}, {lon}'
}

# access child objects
getjson {
    url = 'https://api.icndb.com/jokes/random'
    format = '{value-joke}'
}

# access title from 0th element of articles list
getjson {
    request_url = 'https://newsapi.org/v1/articles?source=bbc-news'
    request_headers = {'X-Api-Key': 'super-secret-newsapi-api-key'}
    format = '{articles-0-title}'
}

# access if top-level object is a list
getjson {
    request_url = 'https://jsonplaceholder.typicode.com/posts/1/comments'
    format = '{0-name}'
}

# air_quality
getjson {
    # Fill in the {UID} and {TOKEN}.
    request_url = 'http://api.waqi.info/feed/@{UID}/?token={TOKEN}'
    format = '\?color=aqi {city_name}: {aqi}'
    cache_timeout = 3600  # hourly rate
    flatten_delimiter = '_'
    parent_key = 'data'
    thresholds = [
        (0, '#009966'), (51, '#FFDE33'), (101, '#FF9933'),
        (151, '#CC0033'), (201, '#660099'), (301, '#7E0023'),
    ]
```

Examples (list):
```
# coin_market
getjson {
    request_url = 'https://api.coinmarketcap.com/v1/ticker/?limit=3'
    format = '{format_json}'
    format_json = '{name} ${price_usd} '
    format_json += '[\?color=percent_change_24h {percent_change_24h}%]'
    thresholds = [(-100, 'bad'), (0, 'good')]
    cache_timeout = 600  # respect 10min rate
}

# bitcoin_price
getjson {
    request_url = 'http://api.bitcoincharts.com/v1/markets.json'
    format = '{format_json}'
    format_json = '[\?if=symbol=coinbaseUSD [\?color=#0cf {symbol}] {close:.2f}]'
    format_json += '[\?if=symbol=coinbaseEUR [\?color=#0cf {symbol}] {close:.2f}]'
    cache_timeout = 900  # respect 15min rate
}

# exchange_rate (USD)
getjson {
    request_url = 'https://www.mycurrency.net/service/rates'
    request_headers = {'User-Agent': 'Mozilla/5.0 py3status'}
    format = '{format_json}'
    format_json = '[\?if=currency_code=USD [\?color=sign&show $]{rate:.3f}]'
    format_json += '[\?if=currency_code=GBP [\?color=sign&show £]{rate:.3f}]'
    format_json += '[\?if=currency_code=JPY [\?color=sign&show ¥]{rate:.3f}]'
    color_sign = '#ffd700'
    cache_timeout = 600  # respect 10min rate
}
```

@author vicyap, lasers

SAMPLE OUTPUT
{'full_text': 'Github: Everything operating normally'}
"""

STRING_ERROR_FORMAT = 'missing format'
STRING_ERROR_URL = 'missing url'
STRING_ERROR_LIST = 'missing format_json'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 60
    flatten_delimiter = '-'
    flatten_intermediates = False
    flatten_parent_key = None
    format = None
    format_json = None
    format_separator = ' '
    parent_key = None
    request_auth = None
    request_cookiejar = None
    request_data = None
    request_headers = None
    request_params = None
    request_timeout = 10
    request_url = None
    thresholds = []

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'url',
                    'new': 'request_url',
                    'msg': 'obsolete parameter, use `request_url`'
                },
                {
                    'param': 'timeout',
                    'new': 'request_timeout',
                    'msg': 'obsolete parameter, use `request_timeout`'
                },
                {
                    'param': 'delimiter',
                    'new': 'flatten_delimiter',
                    'msg': 'obsolete parameter, use `flatten_delimiter`'
                },
            ],
        }

    def post_config_hook(self):
        if not self.format:
            raise Exception(STRING_ERROR_FORMAT)
        if not self.request_url:
            raise Exception(STRING_ERROR_URL)
        placeholders = self.py3.get_placeholders_list(self.format)
        self.init_list = 'format_json' in placeholders
        if self.init_list:
            placeholders.remove('format_json')
            if not self.format_json:
                raise Exception(STRING_ERROR_LIST)
        self.init_dict = bool(len(placeholders))

    def _org_and_man(self, data):
        # organize and manipulate
        data = self.py3.flatten_dict(
            data,
            self.flatten_delimiter,
            self.flatten_intermediates,
            self.flatten_parent_key
        )
        if self.thresholds:
            for k, v in data.items():
                self.py3.threshold_get_color(v, k)
        return data

    def getjson(self):
        format_json = None
        dict_data = {}
        try:
            json_data = self.py3.request(
                self.request_url,
                params=self.request_params,
                data=self.request_data,
                headers=self.request_headers,
                timeout=self.request_timeout,
                auth=self.request_auth,
                cookiejar=self.request_cookiejar,
            ).json()
        except self.py3.RequestException:
            json_data = {}

        if json_data:
            if self.parent_key:
                json_data = json_data.get(self.parent_key)

            if self.init_list:
                new_data = []
                for index, data in enumerate(json_data, 1):
                    data['index'] = index
                    data = self._org_and_man(data)
                    new_data.append(self.py3.safe_format(
                        self.format_json, data))

                format_separator = self.py3.safe_format(
                    self.format_separator)
                format_json = self.py3.composite_join(
                    format_separator, new_data)

            if self.init_dict:
                dict_data = self._org_and_man(json_data)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, dict(
                    format_json=format_json,
                    **dict_data
                )
            )
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
