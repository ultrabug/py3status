# -*- coding: utf-8 -*-
"""
Display cryptocurrency data.

The site offer various types of data such as symbol, trades, volumes,
weighted prices, et cetera for a wide range of cryptocurrencies.
For more information, visit https://bitcoincharts.com

Configuration parameters:
    cache_timeout: refresh interval for this module. A message from the site:
        Don't query more often than once every 15 minutes (default 900)
    format: display format for this module (default '{format_market}')
    format_market: display format for cryptocurrency markets
        (default '{symbol} [\?color=close {close:.2f}]')
    format_separator: show separator if more than one (default ' ')
    markets: specify a list of markets to use
        (default ['coinbaseUSD', 'coinbaseEUR', 'bitstampUSD', 'bitstampEUR'])
    request_timeout: time to wait for a response, in seconds (default 10)
    symbols: if possible, convert `{currency}` abbreviations to symbols
        e.g. USD -> $, EUR -> € and so on (default True)
    thresholds: specify color thresholds to use
        (default [(-1, 'bad'), (0, 'degraded'), (1, 'good')])

    See https://bitcoincharts.com/markets/list/ for a list of markets.

Format placeholders:
    {format_market} format for cryptocurrency markets

    Bitcoincharts offers weighted prices for several currencies.
    Weighted prices are calculated for the last 24 hours, 7 days and 30 days.
    You can use this to price goods and services in Bitcoins. This will yield
    much lower fluctuations than using a single market's latest price.

    To print weighed prices in different currency, replicate the placeholders
    below with a valid option, eg `{usd_24h}`. You can use many as you like.

    {xxx_24h}       eg weighted price for last 24 hours eg 1234.56
    {xxx_7d}        eg weighted price for last  7 days eg 1234.56
    {xxx_30d}       eg weighted price for last 30 days eg 1234.56

    Valid options are: ARS, AUD, BRL, CAD, CHF, CLP, CZK, DKK, EUR, GBP, HKD,
    IDR, ILS, INR, JPY, KRW, MXN, MYR, NGN, NOK, NZD, PKR, PLN, RUB, SEK, SGD,
    SLL, THB, USD, VEF, VND, ZAR... and be written in lowercase.

format_market placeholders:
    {symbol}          short name for market, eg localbtcUSD
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

Color options:
    color_bad: the price has dropped since the last interval
    color_degraded: the price hasn't changed since the last interval
    color_good: the price has increased since the last interval

Color thresholds:
    format_market:
        xxx: print a color based on changes between `xxx` and last `xxx`

DEPRECATION TODO:
    param: field
    old: price = _rate = market[self.field]... to {price}
    new: convert {????} to {price} if self.field is '????'

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
    format_market = '{symbol} [\?color=close {close:.2f}]'
    format_separator = ' '
    markets = ['coinbaseUSD', 'coinbaseEUR', 'bitstampUSD', 'bitstampEUR']
    request_timeout = 10
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
                {
                    'placeholder': 'price',
                    'new': 'close',
                    'format_strings': ['format_market'],
                },
            ],
        }

    def post_config_hook(self):
        if isinstance(self.markets, str):
            self.markets = [x.strip() for x in self.markets.split(',')]
        # end deprecation
        self.last_market = self.py3.storage_get('last_market') or {}
        self.last_weighted = self.py3.storage_get('last_weighted') or {}
        self.init = {
            'markets': self.py3.format_contains(self.format, 'format_market'),
            'weighted_prices': self.py3.format_contains(
                self.format, ['*_24h', '*_30d', '*_7d']),
        }

    def _get_markets(self):
        try:
            data = self.py3.request(
                URL_MARKETS, timeout=self.request_timeout).json()
        except self.py3.RequestException:
            data = {}
        return data

    def _get_weighted_prices(self):
        try:
            data = self.py3.request(
                URL_WEIGHTED_PRICES, timeout=self.request_timeout).json()
            data = {k.lower(): v for k, v in data.items()}
            data = self.py3.flatten_dict(data, '_')
        except self.py3.RequestException:
            data = {}
        return data

    def kill(self):
        self.py3.storage_set('last_market', self.last_market)
        self.py3.storage_set('last_weighted', self.last_weighted)

    def bitcoin_price(self):
        format_market = None
        weighted_prices_data = {}
        markets_data = {}
        new_data = []

        if self.init['markets']:
            markets_data = self._get_markets()

            for name in self.markets:
                for market in markets_data:
                    if name != market['symbol']:
                        continue
                    if name not in self.last_market:
                        self.last_market[name] = {}
                    if self.symbols:
                        sign = market['currency']
                        market['currency'] = MAP.get(sign, sign)

                    for key, value in market.items():
                        result = 0
                        if self.last_market[name].get(key) is None:
                            self.last_market[name][key] = result
                        elif isinstance(value, (int, float)):
                            market_value = market[key]
                            last_market = self.last_market[name][key]
                            if market_value < last_market:
                                result = -1
                            elif market_value > last_market:
                                result = 1
                            self.last_market[name][key] = market_value

                        if self.thresholds:
                            self.py3.threshold_get_color(result, key)

                    new_data.append(self.py3.safe_format(
                        self.format_market, market))
                    break

        format_separator = self.py3.safe_format(self.format_separator)
        format_market = self.py3.composite_join(format_separator, new_data)

        if self.init['weighted_prices']:
            weighted_prices_data = self._get_weighted_prices()
            for k, v in weighted_prices_data.items():
                self.py3.threshold_get_color(v, k)

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
