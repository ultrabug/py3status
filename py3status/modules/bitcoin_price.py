# -*- coding: utf-8 -*-
"""
Display cryptocurrency markets.

The site offer various types of data such as symbol, trades, volumes,
weighted prices, et cetera for a wide range of cryptocurrency markets.
For more information, visit https://bitcoincharts.com

Configuration parameters:
    cache_timeout: refresh interval for this module. A message from the site:
        Don't query more often than once every 15 minutes (default 900)
    format: display format for this module (default '{format_market}')
    format_market: display format for cryptocurrency markets
        (default '{symbol} [\?color=last_close {currency}{close:.2f}]')
    format_separator: show separator if more than one (default ' ')
    markets: specify a list of markets to use
        (default ['coinbaseUSD', 'coinbaseEUR', 'bitstampUSD', 'bitstampEUR'])
    symbols: convert `{currency}` to signs, eg $, €, etc (default True)
    thresholds: specify color thresholds to use
        (default [(-1, 'bad'), (0, 'degraded'), (1, 'good')])

Format placeholders:
    {format_market} format for cryptocurrency markets
    {xxx_24h}       eg weighted price for last 24 hours eg 1234.56
    {xxx_7d}        eg weighted price for last  7 days eg 1234.56
    {xxx_30d}       eg weighted price for last 30 days eg 1234.56

    Bitcoincharts offers weighted prices for several currencies.
    Weighted prices are calculated for the last 24 hours, 7 days and 30 days.
    You can use this to price goods and services in Bitcoins. This will yield
    much lower fluctuations than using a single market's latest price.

    To print weighed prices in different currency, replicate the placeholders
    above with a valid option, eg `{usd_24h}`. You can use many as you like.

    Valid options are: ARS, AUD, BRL, CAD, CHF, CLP, CZK, DKK, EUR, GBP, HKD,
    IDR, ILS, INR, JPY, KRW, MXN, MYR, NGN, NOK, NZD, PKR, PLN, RUB, SEK, SGD,
    SLL, THB, USD, VEF, VND, ZAR... and be written in lowercase.

format_market placeholders:
    {symbol}          alias for market name, eg localbtcUSD
    {currency}        base currency of the market, eg USD, EUR, GBP
    {bid}             highest bid price, eg 1704347.14
    {ask}             lowest ask price, eg 12100.0,
    {avg}             average price, eg 17265.00867749991
    {latest_trade}    unixtime of latest trade, eg 1513072778
    {high}            highest trade during day, eg 68874.32
    {low}             lowest trade during day, eg 11401.79
    {close}           latest trade, eg 24183.56
    {volume}          total trade volume of day in BTC, eg 143.11342831
    {currency_volume} total trade volume of day in currency, eg 2470854.5816389113
    {weighted_price}  weighted price for this day eg 17265.00867749991
    {duration}        duration, eg 89282

Notes:
    See http://bitcoincharts.com/markets/list/ for a list of markets.

Color options:
    color_bad: the price has dropped since the last interval
    color_degraded: the price hasn't changed since the last interval
    color_good: the price has increased since the last interval

Color thresholds:
    format:
        xxx: print a color based on the value of `xxx` placeholder
        last_xxx: print a color based on changes between `xxx` and last `xxx`
    format_market:
        xxx: print a color based on the value of `xxx` placeholder
        last_xxx: print a color based on changes between `xxx` and last `xxx`

Examples:
```
# colorize usd_24h weighted prices
bitcoin_price {
    format = '[{format_market} usd_24h [\?color=last_usd_24h {usd_24h}]]'
}

# round to the nearest dollar
bitcoin_price {
    format_market = '{symbol} [\?color=last_close {close:.0f}]'
}

# remove last 3 letters from symbol, hack
bitcoin_price {
    format_market = '[[\?max_length=-3 {symbol}] '
    format_market += '[\?color=last_close {currency}{close:.2f}]]'
}
```

@author Andre Doser <doser.andre AT gmail.com>, lasers

SAMPLE OUTPUT
[
    {'full_text': 'coinbaseUSD'}, {'full_text': '17139.00', 'color': '#f00'},
    {'full_text': 'coinbaseEUR'}, {'full_text': '14412.76', 'color': '#0f0'},
    {'full_text': 'bitstampUSD'}, {'full_text': '2546.00', 'color': '#ff0'},
    {'full_text': 'bitstampEUR'}, {'full_text': '13649.00', 'color': '#0f0'},
]
"""

URL_MARKETS = 'https://api.bitcoincharts.com/v1/markets.json'
URL_WEIGHTED_PRICES = 'https://api.bitcoincharts.com/v1/weighted_prices.json'
MAP = {'AUD': '$', 'CNY': '¥', 'EUR': '€', 'GBP': '£', 'USD': '$', 'YEN': '¥'}


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 900
    format = '{format_market}'
    format_market = '{symbol} [\?color=last_close {currency}{close:.2f}]'
    format_separator = ' '
    markets = ['coinbaseUSD', 'coinbaseEUR', 'bitstampUSD', 'bitstampEUR']
    symbols = True
    thresholds = [(-1, 'bad'), (0, 'degraded'), (1, 'good')]

    class Meta:
        update_config = {
            'update_placeholder_format': [
                {
                    'placeholder_formats': {
                        'price': ':.2f',
                    },
                    'format_strings': ['format_bitcoin'],
                }
            ],
        }

        def deprecate_function(config):
            if (not config.get('format_separator') and
                    config.get('bitcoin_separator')):
                sep = config.get('bitcoin_separator')
                sep = sep.replace('\\', '\\\\')
                sep = sep.replace('[', '\[')
                sep = sep.replace(']', '\]')
                sep = sep.replace('|', '\|')

                return {'format_separator': sep}
            else:
                return {}

        deprecated = {
            'function': [
                {
                    'function': deprecate_function,
                },
            ],
            'remove': [
                {
                    'param': 'bitcoin_separator',
                    'msg': 'obsolete set using `format_separator`',
                },
                {
                    'param': 'hide_on_error',
                    'msg': 'obsolete param',
                },
            ],
            'rename': [
                {
                    'param': 'format_bitcoin',
                    'new': 'format_market',
                    'msg': 'obsolete parameter use `format_market`',
                },
            ],
            'rename_placeholder': [
                {
                    'placeholder': 'format_bitcoin',
                    'new': 'format_market',
                    'format_strings': ['format'],
                },
            ],
        }

    def post_config_hook(self):
        # start deprecation
        self.field = getattr(self, 'field', 'close')
        self.price = self.py3.format_contains(self.format_market, 'price*')
        if isinstance(self.markets, str):
            self.markets = [x.strip() for x in self.markets.split(',')]
        # end deprecation
        self.init = {}
        self.placeholders = {}
        self.last_data = self.py3.storage_get('last_data') or {}
        self.request_timeout = 10
        init_policies = [
            # names, format contains placeholders, format_string
            ('markets', 'format_market', self.format_market),
            ('weighted_prices', ['*_24h', '*_30d', '*_7d'], self.format)
        ]
        for x in init_policies:
            self.init[x[0]] = self.py3.format_contains(self.format, x[1])
            self.placeholders[x[0]] = self.py3.get_placeholders_list(x[2])

    def _get_markets_data(self):
        try:
            data = self.py3.request(
                URL_MARKETS, timeout=self.request_timeout).json()
        except self.py3.RequestException:
            data = {}
        return data

    def _get_weighted_prices_data(self):
        try:
            data = self.py3.request(
                URL_WEIGHTED_PRICES, timeout=self.request_timeout).json()
            data = {k.lower(): v for k, v in data.items()}
            data = self.py3.flatten_dict(data, '_')
        except self.py3.RequestException:
            data = {}
        return data

    def _manipulate(self, data, placeholders, name):
        for key in placeholders:
            if key not in data:
                continue
            result = 0
            value = data[key]
            self.last_data.setdefault(name, {})
            if name == 'weighted_prices':
                value = float(value)
            if isinstance(value, (int, float)):
                last_value = self.last_data[name].get(key)
                self.last_data[name][key] = value
                if last_value is not None:
                    if value < last_value:
                        result = -1
                    elif value > last_value:
                        result = 1
            # it went down? bad. it went up? good. otherwise, degraded.
            if self.thresholds:
                self.py3.threshold_get_color(value, key)
                self.py3.threshold_get_color(result, 'last_' + key)

    def kill(self):
        self.py3.storage_set('last_data', self.last_data)

    def bitcoin_price(self):
        format_market = None
        weighted_prices_data = {}
        markets_data = {}

        if self.init['markets']:
            markets_data = self._get_markets_data()
            new_market = []

            for name in self.markets:
                for market in markets_data:
                    # skip nonmatched markets
                    if name != market['symbol']:
                        continue
                    # deprecation: show field->price + market==symbol
                    if self.price:
                        market['market'] = market['symbol']
                        sign = market['currency']
                        market['symbol'] = MAP.get(sign, sign)
                        if self.field in market:
                            market['price'] = market[self.field]
                    # end deprecation
                    # convert {currency} abbrevs to symbols
                    if self.symbols:
                        sign = market['currency']
                        market['currency'] = MAP.get(sign, sign)
                    # waste not, want not
                    self._manipulate(market, self.placeholders['markets'], name)
                    new_market.append(
                        self.py3.safe_format(self.format_market, market)
                    )
                    break

            format_separator = self.py3.safe_format(self.format_separator)
            format_market = self.py3.composite_join(format_separator, new_market)

        if self.init['weighted_prices']:
            weighted_prices_data = self._get_weighted_prices_data()
            self._manipulate(
                weighted_prices_data,
                self.placeholders['weighted_prices'],
                'weighted_prices'
            )

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, dict(
                    format_market=format_market,
                    **weighted_prices_data
                )
            )
        }


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
