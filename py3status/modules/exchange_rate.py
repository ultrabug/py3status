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

@author tobes
@license BSD

SAMPLE OUTPUT
{'full_text': u'$1.0617 \xa30.8841 \xa5121.5380'}
"""

import re

URL = 'http://query.yahooapis.com/v1/public/yql?'
URL += 'q=select * from yahoo.finance.xchange where pair in ({currencies})'
URL += '&env=store://datatables.org/alltableswithkeys&format=json'


class Py3status:
    base = 'EUR'
    cache_timeout = 600
    format = u'${USD} £{GBP} ¥{JPY}'

    def post_config_hook(self):
        self.request_timeout = 20

        self.currencies = re.findall('\{([^}]*)\}', self.format)
        # create url
        currencies = ['"%s%s"' % (self.base, cur) for cur in self.currencies]
        self.data_url = URL.format(currencies=','.join(currencies))
        # cache for rates data as sometimes we do not receive valid data
        self.rates_data = {currency: '?' for currency in self.currencies}

    def rates(self):
        try:
            result = self.py3.request(self.data_url, timeout=self.request_timeout)
        except (self.py3.RequestException):
            result = None
        rates = []
        if result:
            data = result.json()
            try:
                rates = data['query']['results']['rate']
            except (KeyError, TypeError):
                pass

        # Single currency is not passed as a 1 element list
        if isinstance(rates, list):
            for rate in rates:
                self.rates_data[rate['id'][3:]] = rate['Rate']
        else:
            self.rates_data[rates['id'][3:]] = rates['Rate']

        return {
            'full_text': self.py3.safe_format(self.format, self.rates_data),
            'cached_until': self.py3.time_in(self.cache_timeout),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
