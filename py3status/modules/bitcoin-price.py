# -*- coding: utf-8 -*-
"""
Module for displaying bitcoin prices using
the API by www.bitcoincharts.com.

Written and contributed by @tasse:
    Andre Doser <doser.andre AT gmail.com>
"""
import json
from time import time


class Py3status:
    """
    Configuration parameters:
        - cache_timeout: Should be at least 15 min according to bitcoincharts.
        - color_index  : Index of the market responsible for coloration,
                         meaning that the output is going to be green if the
                         price went up and red if it went down.
                         default: -1 means no coloration,
                                  except when only one market is selected
        - field        : Field that is displayed per market,
                         see http://bitcoincharts.com/about/markets-api/
        - markets      : Comma-separated list of markets. Supported markets can
                         be found at http://bitcoincharts.com/markets/list/
        - symbols      : Try to match currency abbreviations to symbols,
                         e.g. USD -> $, EUR -> € and so on
    """
    cache_timeout = 900
    color_index = -1
    field = 'closse'
    markets = 'btceEUR, btcdeEUR'
    symbols = True

    def __init__(self):
        """
        Initialize last_price, set the currency mapping
        and the url containing the data.
        """
        self.last_price = 0
        self.currency_map = {'EUR': '€', 'USD': '$', 'GBP': '£',
                             'YEN': '¥', 'CNY': '¥', 'AUD': '$'}
        self.url = 'http://api.bitcoincharts.com/v1/markets.json'

    def _get_price(self, data, market, field):
        """
        Given the data (in json format), returns the
        field for a given market.
        """
        for m in data:
            if m['symbol'] == market:
                return m[field]

    def get_rate(self, i3s_output_list, i3s_config):
        response = {'full_text': '', 'name': 'bitcoin rates',
                    'cached_until': time() + self.cache_timeout}
        try:  # python 3
            from urllib.request import urlopen
            from urllib.error import URLError
        except ImportError:  # python 2
            from urllib2 import urlopen
            from urllib2 import URLError
        # get the data from the bitcoincharts website
        try:
            data = json.loads(urlopen(self.url).read().decode())
        except URLError:
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
                if i == self.color_index:  # coloration
                    color_rate = rate
            except KeyError:
                continue
            out = market[:-3] if rate else market  # market name
            out += ': '
            out += 'N/A' if not rate else '{:.2f}'.format(rate)     # rate
            currency_sym = self.currency_map.get(market[-3:], market[-3:])
            out += currency_sym if self.symbols else market
            rates.append(out)
        # only colorize if an index is given or
        # if only one market is selected
        if len(rates) == 1 or self.color_index > -1:
            if self.last_price == 0:
                pass
            elif color_rate < self.last_price:
                response['color'] = i3s_config['color_bad']
            elif color_rate > self.last_price:
                response['color'] = i3s_config['color_good']
            self.last_price = color_rate
        response['full_text'] = ', '.join(rates)
        return response

if __name__ == '__main__':
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.get_rate([], {'color_good': 'green',
                              'color_bad': 'red'}))
        sleep(5)
