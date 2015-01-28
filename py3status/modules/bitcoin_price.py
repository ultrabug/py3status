# -*- coding: utf-8 -*-
"""
Module for displaying bitcoin prices using
the API by www.bitcoincharts.com.

Written and contributed by @tasse:
    Andre Doser <doser.andre AT gmail.com>
"""
import json

from time import time
try:
    # python 3
    from urllib.error import URLError
    from urllib.request import urlopen
except ImportError:
    # python 2
    from urllib2 import URLError
    from urllib2 import urlopen


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
        - hide_on_error: Display empty response if True, else an error message
        - markets      : Comma-separated list of markets. Supported markets can
                         be found at http://bitcoincharts.com/markets/list/
        - symbols      : Try to match currency abbreviations to symbols,
                         e.g. USD -> $, EUR -> € and so on
    """

    # available configuration parameters
    cache_timeout = 900
    color_index = -1
    field = 'close'
    hide_on_error = False
    markets = 'btceUSD, btcdeEUR'
    symbols = True

    def __init__(self):
        """
        Initialize last_price, set the currency mapping
        and the url containing the data.
        """
        self.currency_map = {
            'AUD': '$',
            'CNY': '¥',
            'EUR': '€',
            'GBP': '£',
            'USD': '$',
            'YEN': '¥'
        }
        self.last_price = 0
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
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }

        # get the data from the bitcoincharts website
        try:
            data = json.loads(urlopen(self.url).read().decode())
        except URLError:
            if not self.hide_on_error:
                response['color'] = i3s_config['color_bad']
                response['full_text'] = 'Bitcoincharts unreachable'
            return response

        # get the rate for each market given
        rates, markets = [], self.markets.split(',')
        color_rate = None
        for i, market in enumerate(markets):
            market = market.strip()
            try:
                rate = self._get_price(data, market, self.field)
                # coloration
                if i == self.color_index or len(markets) == 1:
                    color_rate = rate
            except KeyError:
                continue
            # market name
            out = market[:-3] if rate else market
            out += ': '
            # rate
            out += 'N/A' if not rate else '{:.2f}'.format(rate)
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
        print(x.get_rate([], {'color_good': 'green', 'color_bad': 'red'}))
        sleep(5)
