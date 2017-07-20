# -*- coding: utf-8 -*-

""" Display CryptoCurrency using coinmarketcap.com

Configuration parameters:
    cache_timeout: refresh interval for this module. A advise from the site:
        "Please limit requests to no more than 10 per minute." (default 600)
    coin_separator: display separator if more than one (default ', ')
    coin_symbols: coin symbol that will display price (default {'btc', 'eth', 'xrp'})
    convert: currency unit want to display (default 'usd')
    format: display format for this module (default '{format_coin}')
    format_coin: display format for coins (default '{name}: {price}{symbol} ({percentage})')
    rounds: The value to round (default 2)

    format_coin placeholders:
        {format_coin} format for coins

    format_coin placeholders:
        {name} coin's name (ex. bitcoin - btc, ethereum - eth)
        {price} current prices
        {symbol} currency symbols
        {percentage} increment/decrement percentage during 24 hours
"""

import json

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


class Py3status:
    cache_timeout = 600
    coin_separator = ', '
    coin_symbols = {'btc', 'eth', 'xrp'}
    convert = 'usd'
    format = "{format_coin}"
    format_coin = "{name}: {price}{symbol} ({percentage})"
    rounds = 2

    def post_config_hook(self):
        self.ticker = "https://api.coinmarketcap.com/v1/ticker/?convert={}".format(self.convert)

        self.currency_map = {
            'krw': '₩',
            'aud': '$',
            'cny': '¥',
            'eur': '€',
            'gbp': '£',
            'usd': '$',
            'jpy': '¥'
        }

        self.convert = self.convert.lower()

    def _get_coin_info(self, currencies, coin_symbol):
        for currency in currencies:
            if currency['symbol'] == coin_symbol or currency['symbol'].lower() == coin_symbol:
                return {
                    'name': currency['name'],
                    'price_{}'.format(self.convert): currency['price_{}'.format(self.convert)],
                    'percent_change_24h': currency['percent_change_24h']
                }

    def all_currency(self):
        currencies = json.loads(urlopen(self.ticker).read().decode())
        out_text = list()

        for coin in self.coin_symbols:
            coin_info = self._get_coin_info(currencies, coin.strip())

            try:
                _name = coin_info['name']
            except TypeError:
                continue

            _price = coin_info['price_{}'.format(self.convert)]
            _percentage = coin_info['percent_change_24h']
            _symbol = self.currency_map[self.convert]

            _price = '{}'.format(round(float(_price), self.rounds))
            _percentage = float(_percentage)

            if _percentage > 0:
                _percentage = '+{}%'.format(_percentage)
            else:
                _percentage = '{}%'.format(_percentage)

            out_text.append(self.py3.safe_format(
                self.format_coin, {
                    'name': _name,
                    'price': _price,
                    'symbol': _symbol,
                    'percentage': _percentage})
            )

        out_text = self.py3.composite_join(self.coin_separator, out_text)

        response = {'cached_until': self.py3.time_in(self.cache_timeout)}
        response['full_text'] = self.py3.safe_format(self.format, {'format_coin': out_text})

        return response


if __name__ == "__main__":
    from py3status.module_test import module_test
    module_test(Py3status)
