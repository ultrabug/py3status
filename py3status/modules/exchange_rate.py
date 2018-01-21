# -*- coding: utf-8 -*-
"""
Display foreign exchange rates.

The exchange rate data comes from https://www.mycurrency.net/service/rates

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
{'full_text': u'$1.061 \xa30.884 \xa5121.538'}
"""

URL = 'https://www.mycurrency.net/service/rates'
UA = 'Mozilla/5.0 py3status'


class Py3status:
    """
    """
    # available configuration parameters
    base = 'EUR'
    cache_timeout = 600
    format = u'${USD} £{GBP} ¥{JPY}'

    def post_config_hook(self):
        self.request_timeout = 20
        self.currencies = self.py3.get_placeholders_list(self.format)
        # set the default precision
        default_formats = {x: ':.3f' for x in self.currencies}
        self.format = self.py3.update_placeholder_formats(
            self.format, default_formats
        )
        self.rates_data = {currency: '?' for currency in self.currencies}
        self.headers = {'User-Agent': UA}

    def rates(self):
        try:
            result = self.py3.request(
                URL, timeout=self.request_timeout, headers=self.headers
            )
        except self.py3.RequestException:
            result = None
        rates = {}
        if result:
            data = result.json()
            for item in data:
                rates[item['currency_code']] = item['rate']
            base_rate = 1.0 / rates.get(self.base)
            for currency in self.currencies:
                try:
                    rate = rates[currency] * base_rate
                except:
                    rate = '?'
                self.rates_data[currency] = rate

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
