# -*- coding: utf-8 -*-
"""
Module for displaying bitcoin prices.

Written and contributed by @tasse:
    Andre Doser <doser.andre AT gmail.com>
"""
# -*- coding: utf-8 -*-
"""
Module for displaying bitcoin prices.
"""
import json
import urllib.request as ul
from time import time
import re

last_price = 0


class Py3status:
    # btc-e, api,bitfinex, bitstamp, bitpay
    websites = 'btc-e'
    value = 'last'
    cache_timeout = 120

    def __init__(self):
        self._hoster = {'https://btc-e.com/api/2/btc_usd/ticker': self._get_btce,
                        'https://bitstamp.net/api/ticker/': self._get_bitstamp,
                        'https://api.bitfinex.com/v1/pubticker/BTCUSD': self._get_bitfinex,
                        'https://bitpay.com/api/rates': self._get_bitpay}

    # returns the price for a given site in USD
    # value is elem of {high, low, avg, last}
    def _get_btce(self, url, value):
        try:
            data = json.loads(ul.urlopen(url).read().decode())
            # default is 'last' price
            value = data['ticker'].get(value, data['ticker']['last'])
        except:
            value = 'N/A'
        return 'BTC-e', value

    def _get_bitstamp(self, url, value):
        # bitstamp API is different in the following
        if value == 'avg':
            value = 'vwap'
        try:
            data = json.loads(ul.urlopen(url).read().decode())
            value = data.get(value, data['last'])
        except:
            value = 'N/A'
        return 'BS', value

    def _get_bitfinex(self, url, value):
        # bitfinex API is different in the following
        if value == 'avg':
            value = 'mid'
        if value == 'last':
            value = 'last_price'
        try:
            data = json.loads(ul.urlopen(url).read().decode())
            value = data.get(value, data['last_price'])
        except:
            value = 'N/A'
        return 'BF', value

    def _get_bitpay(self, url, value):
        try:
            data = json.loads(ul.urlopen(url).read().decode())
            value = [x['rate'] for x in data if x['code'] == 'USD'][0]
        except:
            value = 'N/A'
        return 'BP', value

    def get_rate(self, i3s_output_list, i3s_config):
        response = {'full_text': '', 'name': 'bitcoin rates',
                    'cached_until': time() + self.cache_timeout}
        rates = []
        cnt = 0
        for url, f in self._hoster.items():
            rgx = re.search('.*//(.*)\..*', url).group(1)
            if rgx not in self.websites:
                continue
            name, rate = f(url, self.value)
            rates.append('{}: '.format(name)
                         + ('N/A' if rate == 'N/A'
                             else ('{:.2f}$'.format(float(rate)))))
            cnt += 1
        # don't color multiple sites
        global last_price
        if cnt == 1:
            if last_price == 0:
                pass
            elif rate < last_price:
                response['color'] = i3s_config['color_bad']
            elif rate > last_price:
                response['color'] = i3s_config['color_good']
            last_price = rate
        response['full_text'] = ', '.join(rates)
        return response

if __name__ == '__main__':
    from time import sleep
    x = Py3status()
    while True:
        print(x.get_rate([], {'color_good': 'green',
                              'color_bad': 'red'}))
        sleep(1)
