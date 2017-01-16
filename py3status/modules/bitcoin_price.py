# -*- coding: utf-8 -*-
# FIXME color_index param
"""
Display bitcoin prices using bitcoincharts.com.

Configuration parameters:
    cache_timeout: Should be at least 15 min according to bitcoincharts.
        (default 900)
    color_index: Index of the market responsible for coloration,
        -1 means no coloration, except when only one market is selected
        (default -1)
    field: Field that is displayed per market,
        see http://bitcoincharts.com/about/markets-api/ (default 'close')
    hide_on_error: Display empty response if True, else an error message
         (default False)
    markets: Comma-separated list of markets. Supported markets can
        be found at http://bitcoincharts.com/markets/list/
         (default 'btceUSD, btcdeEUR')
    symbols: Try to match currency abbreviations to symbols,
        e.g. USD -> $, EUR -> € and so on (default True)

Color options:
    color_bad:  Price has dropped or not available
    color_good: Price has increased

@author Andre Doser <doser.andre AT gmail.com>

SAMPLE OUTPUT
{'full_text': u'btce: 809.40$, btcde: 785.00\u20ac'}
"""
import json

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

    def get_rate(self):
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': ''
        }

        # get the data from the bitcoincharts website
        try:
            data = json.loads(urlopen(self.url).read().decode())
        except URLError:
            if not self.hide_on_error:
                response['color'] = self.py3.COLOR_BAD
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
                response['color'] = self.py3.COLOR_BAD
            elif color_rate > self.last_price:
                response['color'] = self.py3.COLOR_GOOD
            self.last_price = color_rate

        response['full_text'] = ', '.join(rates)
        return response


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
