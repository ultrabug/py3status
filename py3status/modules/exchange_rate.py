"""
Display foreign exchange rates.

Configuration parameters:
    api_key: the exchangeratesapi.io API access key (default None)
    base: specify base currency to use for exchange rates (default 'EUR')
    cache_timeout: refresh interval for this module (default 600)
    format: display format for this module (default '${USD} £{GBP} ¥{JPY}')

Format placeholders:
    See https://api.exchangeratesapi.io/latest for a full list of foreign
    exchange rates published by the European Central Bank. Not all of exchange
    rates will be available. Also, see https://en.wikipedia.org/wiki/ISO_4217

@author tobes
@license BSD

SAMPLE OUTPUT
{'full_text': u'$1.061 \xa30.884 \xa5121.538'}
"""


class Py3status:
    """ """

    # available configuration parameters
    api_key = None
    base = "EUR"
    cache_timeout = 600
    format = "${USD} £{GBP} ¥{JPY}"

    def post_config_hook(self):
        # Verify the API key
        if self.api_key is None:
            raise Exception(
                "API Key for ExchangeRatesApi.io cannot be empty!"
                " Go to https://exchangeratesapi.io/pricing/"
                " get an API Key."
            )
        self.url = f"http://api.exchangeratesapi.io/v1/latest?base={self.base}"
        self.url += f"&access_key={self.api_key}"
        placeholders = self.py3.get_placeholders_list(self.format)
        formats = dict.fromkeys(placeholders, ":.3f")
        self.format = self.py3.update_placeholder_formats(self.format, formats)
        self.rate_data = dict.fromkeys(placeholders, "?")

    def _get_exchange_rates(self):
        try:
            response = self.py3.request(self.url)
        except self.py3.RequestException:
            return {}
        data = response.json()
        if data and data["success"]:
            data = data.get("rates", {})
        else:
            error = data.get("error")
            if error:
                self.py3.error(error["info"])
        return data

    def exchange_rate(self):
        self.rate_data.update(self._get_exchange_rates())

        return {
            "full_text": self.py3.safe_format(self.format, self.rate_data),
            "cached_until": self.py3.time_in(self.cache_timeout),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
