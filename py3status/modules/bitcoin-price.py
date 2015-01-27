# -*- coding: utf-8 -*-
"""
Module for displaying bitcoin prices using
the API by www.bitcoincharts.com.

Written and contributed by @tasse:
    Andre Doser <doser.andre AT gmail.com>
"""
import json
from time import time

last_price = 0


class Py3status:
    # possible markets see http://bitcoincharts.com/markets/list/
    cache_timeout = 900  # load max. every 15 min (according to bitcoincharts)
    color_index = -1
    field = 'close'
    markets = 'btceEUR, btcdeEUR'
    symbols = True

    _map = {'EUR': '€', 'USD': '$', 'GBP': '£', 'YEN': '¥', 'CNY': '¥',
            'AUD': '$'}
    _url = 'http://api.bitcoincharts.com/v1/markets.json'

    def _get_price(self, data, market, field):
        for m in data:
            if m['symbol'] == market:
                return m[field]

    def get_rate(self, i3s_output_list, i3s_config):
        response = {'full_text': '', 'name': 'bitcoin rates',
                    'cached_until': time() + self.cache_timeout}
        try:  # python 3
            import urllib.request as ul
        except:  # python 2
            import urllib2 as ul
        # get the data from the bitcoincharts website
        try:
            data = json.loads(ul.urlopen(self._url).read().decode())
        except Exception:
            response['color'] = i3s_config['color_bad']
            response['full_text'] = 'Bitcoincharts not reachable'
            return response
        # get the rate for each market given
        rates, markets = [], self.markets.split(",")
        color_rate = None
        for i, market in enumerate(markets):
            market = market.strip()
            try:
                rate = self._get_price(data, market, self.field)
                if i == self.color_index:
                    color_rate = rate
            except Exception:
                pass
            out = market[:-3] if rate else market  # market name
            out += ': '
            out += 'N/A' if not rate else '{:.2f}'.format(rate)     # rate
            currency_sym = self._map.get(market[-3:], market[-3:])
            out += currency_sym if self.symbols else market
            rates.append(out)
        # don't color multiple sites if no color_index is given
        global last_price
        if len(rates) == 1 or self.color_index > -1:
            if last_price == 0:
                pass
            elif color_rate < last_price:
                response['color'] = i3s_config['color_bad']
            elif color_rate > last_price:
                response['color'] = i3s_config['color_good']
            last_price = color_rate
        response['full_text'] = ', '.join(rates)
        return response

if __name__ == '__main__':
    from time import sleep
    x = Py3status()
    while True:
        print(x.get_rate([], {'color_good': 'green',
                              'color_bad': 'red'}))
        sleep(5)
        break
