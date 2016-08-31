# -*- coding: utf-8 -*-
"""
Display foreign exchange rates.

The exchange rate data comes from Yahoo Finance.

For a list of three letter currency codes please see
https://en.wikipedia.org/wiki/ISO_4217 NOTE: Not all listed currencies may be
available

Configuration parameters:
    base: Base currency used for exchange rates (default 'EUR')
    cache_timeout: How often we refresh this module in seconds (default 600)
    format: Format of the output.  This is also where requested currencies are
        configured. Add the currency code surrounded by curly braces and it
        will be replaced by the current exchange rate.
        (default '${USD} £{GBP} ¥{JPY}')

Requires:
    requests: python lib

@author tobes
@license BSD
"""

import re
import requests

URL = 'http://query.yahooapis.com/v1/public/yql?'
URL += 'q=select * from yahoo.finance.xchange where pair in ({currencies})'
URL += '&env=store://datatables.org/alltableswithkeys&format=json'


class Py3status:
    base = 'EUR'
    cache_timeout = 600
    format = u'${USD} £{GBP} ¥{JPY}'

    def __init__(self):
        self._initialized = False
        self.request_timeout = 10

    def _init(self):
        self.currencies = re.findall('\{([^}]*)\}', self.format)
        currencies = ['"%s%s"' % (self.base, cur) for cur in self.currencies]
        self.data_url = URL.format(currencies=','.join(currencies))
        self._initialized = True

    def rates(self):
        if not self._initialized:
            self._init()

        try:
            result = requests.get(self.data_url, timeout=self.request_timeout)
        except requests.ConnectionError:
            result = None
        except requests.ReadTimeout:
            result = None
        rates = []
        if result:
            data = result.json()
            try:
                rates = data['query']['results']['rate']
            except KeyError:
                pass
        output = {}
        # Single currency is not passed as a 1 element list
        if isinstance(rates, list):
            for rate in rates:
                output[rate['id'][3:]] = rate['Rate']
        else:
            output[rates['id'][3:]] = rates['Rate']
        for currency in self.currencies:
            if currency not in output:
                output[currency] = '?'
        return {
            'full_text': self.py3.safe_format(self.format, output),
            'cached_until': self.py3.time_in(self.cache_timeout),
        }

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
