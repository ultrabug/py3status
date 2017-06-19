# -*- encoding: utf-8 -*-

import json

try:
    from urllib.error import URLError
    from urllib.request import urlopen
except ImportError:
    from urllib2 import URLError
    from urllib2 import urlopen

class Py3status:
    coin_symbols = "btc, eth, xrp"
    convert = 'usd'
    cache_timeout = 300
    format = "{format_coin}"
    format_coin = "{id}: {price}{symbol} ({percentage})"

    def post_config_hook(self):
        self.ticker_url = "https://api.coinmarketcap.com/v1/ticker/?convert={}".format(self.convert)

        self.currency_map = {
            'krw': '₩',
            'aud': '$',
            'cny': '¥',
            'eur': '€',
            'gbp': '£',
            'usd': '$',
            'yen': '¥'
       } 

        self.convert = self.convert.lower()

    def _get_coin_info(self, currencies, coin_symbol):
        for currency in currencies:
            if currency['symbol'] == coin_symbol or currency['symbol'].lower() == coin_symbol:
                return {
                        'id': currency['id'],
                        'price_{}'.format(self.convert): currency['price_{}'.format(self.convert)],
                        'percent_change_24h': currency['percent_change_24h']
                }
            
    def all_currency(self):
        currencies = json.loads(urlopen(self.ticker_url).read().decode())
        out_text = list()

        for coin in self.coin_symbols.split(','):
            coin_info = self._get_coin_info(currencies, coin.strip())

            _id = coin_info['id']
            _price = coin_info['price_{}'.format(self.convert)]
            _percentage = coin_info['percent_change_24h']
            _symbol = self.currency_map[self.convert]

            out_text.append(self.py3.safe_format(
                self.format_coin, {'id': _id, 'price': _price, 'symbol': _symbol, 'percentage': _percentage})
            )
        
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}
        response['full_text'] = self.py3.safe_format(self.format, {'format_coin': out_text})
        return response
        
if __name__ == "__main__":
    from py3status.module_test import module_test

    config = {
        'convert': 'KRW'
    }

    module_test(Py3status, config=config)
