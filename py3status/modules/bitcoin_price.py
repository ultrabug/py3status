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
        (default ['coinbaseUSD', 'coinbaseEUR', 'btceUSD', 'btcdeEUR'])
    request_timeout: time to wait for a response, in seconds (default 10)
    symbols: if possible, convert `{currency}` abbreviations to symbols
        e.g. USD -> $, EUR -> € and so on (default True)
    thresholds: specify thresholds for changes between updates
        (default [(-1, 'bad'), (0, 'degraded'), (1, 'good')])

    See https://bitcoincharts.com/markets/list/ for a list of markets.

Format placeholders:
    {format_market} format for cryptocurrency markets
    {xxx_24h}       eg weighted price for last 24 hours eg (new output here)
    {xxx_7d}        eg weighted price for last 7 days eg (new output here)
    {xxx_30d}       eg weighted price for last 30 days eg (new output here)

    Bitcoincharts offers weighted prices for several currencies.
    Weighted prices are calculated for the last 24 hours, 7 days and 30 days.
    You can use this to price goods and services in Bitcoins. This will yield
    much lower fluctuations than using a single market's latest price.

    To print weighed prices in different currency, replicate the placeholders
    below with a valid option, eg `{usd_24h}`. You can use many as you like.

    Valid options are: ARS, AUD, BRL, CAD, CHF, CLP, CZK, DKK, EUR, GBP, HKD,
    IDR, ILS, INR, JPY, KRW, MXN, MYR, NGN, NOK, NZD, PKR, PLN, RUB, SEK, SGD,
    SLL, THB, USD, VEF, VND, ZAR... and be written in lowercase.

format_market placeholders:
    {symbol}          short name for market, eg localbtcUSD
    {currency}        base currency of the market, eg USD, EUR, RUB, JPY, etc
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
    color_bad: the price has dropped since the last interval.
    color_degraded: the price hasn't changed since the last interval.
    color_good: the price has increased since the last interval.

Color thresholds:
    format_market:
        `placeholder`: print a color based on the value of `{placeholder}`

DEPRECATION TODO:
    param: field
    old: price = _rate = market[self.field]... to {price}
    new: convert {????} to {price} if self.field is '????'
    May be hard to deprecate some things here.

@author Andre Doser <doser.andre AT gmail.com>, lasers

SAMPLE OUTPUT
[
    {'full_text': 'coinbaseUSD'}, {'full_text': '17139.00', 'color': '#f00'},
    {'full_text': 'coinbaseEUR'}, {'full_text': '14412.76', 'color': '#0f0'},
    {'full_text': 'btceUSD'}, {'full_text': '2546.00', 'color': '#ff0'},
    {'full_text': 'btcdeEUR'}, {'full_text': '13649.00', 'color': '#0f0'},
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
    markets = ['coinbaseUSD', 'coinbaseEUR', 'btceUSD', 'btcdeEUR']
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
        # END DEPRECATION
        self.last_market = {}
        self.last_weighted = {}
        self.request_timeout = 10
        placeholders = self.py3.get_placeholders_list(self.format_market)
        for index, x in enumerate(self.markets, 1):
            self.last_market[index] = {x: None for x in placeholders}
        self.init_markets = self.py3.format_contains(
            self.format, 'format_market')
        self.init_weighted_prices = self.py3.format_contains(
            self.format, ['*_24h', '*_30d', '*_7d'])

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

    def bitcoin_price(self):
        format_market = None
        weighted_prices_data = {}
        markets_data = {}
        new_data = []

        if self.init_markets:
            markets_data = self._get_markets()
        if self.init_weighted_prices:
            weighted_prices_data = self._get_weighted_prices()

        for index, symbol in enumerate(self.markets, 1):
            for market in markets_data:
                if symbol == market['symbol']:
                    if self.symbols:
                        sign = market['currency']
                        market['currency'] = MAP.get(sign, sign)

                    for k, v in self.last_market[index].items():
                        if self.last_market[index][k] is None:
                            self.last_market[index][k] = 0
                        elif isinstance(market[k], (int, float)):
                            market_value = float(market[k])
                            last_market = float(self.last_market[index][k])
                            result = 0
                            if market_value < last_market:
                                result = -1
                            elif market_value > last_market:
                                result = 1
                            if self.thresholds:
                                self.py3.threshold_get_color(result, k)
                            self.last_market[index][k] = market_value

                    new_data.append(self.py3.safe_format(
                        self.format_market, market))
                    break

        format_separator = self.py3.safe_format(self.format_separator)
        format_market = self.py3.composite_join(format_separator, new_data)

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
