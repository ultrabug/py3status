# FIXME color_index param
"""
Display bitcoin using bitcoincharts.com.

Configuration parameters:
    cache_timeout: refresh interval for this module. A message from
        the site: Don't query more often than once every 15 minutes
        (default 900)
    color_index: Index of the market responsible for coloration,
        -1 means no coloration, except when only one market is selected
        (default -1)
    field: Field that is displayed per market,
        see https://bitcoincharts.com/about/markets-api/ (default 'close')
    format: display format for this module (default '{format_bitcoin}')
    format_bitcoin: display format for bitcoin (default '{market}: {price}{symbol}')
    format_separator: show separator if more than one (default ', ')
    hide_on_error: show error message (default False)
    markets: list of supported markets https://bitcoincharts.com/markets/list/
        (default 'btceUSD, btcdeEUR')
    symbols: if possible, convert currency abbreviations to symbols
        e.g. USD -> $, EUR -> € and so on (default True)

Format placeholders:
    {format_bitcoin} format for bitcoin

format_bitcoin placeholders:
    {market} market names
    {price} current prices
    {symbol} currency symbols

Color options:
    color_bad: Price has dropped or not available
    color_good: Price has increased

@author Andre Doser <doser.andre AT gmail.com>

SAMPLE OUTPUT
{'full_text': u'btce: 809.40$, btcde: 785.00\u20ac'}
"""

STRING_UNAVAILABLE = "N/A"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 900
    color_index = -1
    field = "close"
    format = "{format_bitcoin}"
    format_bitcoin = "{market}: {price}{symbol}"
    format_separator = ", "
    hide_on_error = False
    markets = "btceUSD, btcdeEUR"
    symbols = True

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {"price": ":.2f"},
                    "format_strings": ["format_bitcoin"],
                }
            ]
        }

        def deprecate_function(config):
            if not config.get("format_separator") and config.get("bitcoin_separator"):
                sep = config.get("bitcoin_separator")
                sep = sep.replace("\\", "\\\\")
                sep = sep.replace("[", r"\[")
                sep = sep.replace("]", r"\]")
                sep = sep.replace("|", r"\|")

                return {"format_separator": sep}
            else:
                return {}

        deprecated = {
            "function": [{"function": deprecate_function}],
            "remove": [
                {
                    "param": "bitcoin_separator",
                    "msg": "obsolete set using `format_separator`",
                }
            ],
        }

    def post_config_hook(self):
        """
        Initialize last_price, set the currency mapping
        and the url containing the data.
        """
        self.currency_map = {
            "AUD": "$",
            "CNY": "¥",
            "EUR": "€",
            "GBP": "£",
            "USD": "$",
            "YEN": "¥",
        }
        self.last_price = 0
        self.url = "http://api.bitcoincharts.com/v1/markets.json"

    def _get_price(self, data, market, field):
        """
        Given the data (in json format), returns the
        field for a given market.
        """
        for m in data:
            if m["symbol"] == market:
                return m[field]

    def bitcoin_price(self):
        response = {
            "full_text": "",
            "cached_until": self.py3.time_in(self.cache_timeout),
        }

        # get the data from bitcoincharts api
        try:
            data = self.py3.request(self.url).json()
        except self.py3.RequestException as err:
            if self.hide_on_error:
                return response
            self.py3.error(str(err))

        # get the rate for each market given
        color_rate, rates, markets = None, [], self.markets.split(",")
        for i, market in enumerate(markets):
            market = market.strip()
            try:
                rate = self._get_price(data, market, self.field)
                # coloration
                if i == self.color_index or len(markets) == 1:
                    color_rate = rate
            except KeyError:
                continue

            # market/price/symbol
            _market = market[:-3] if rate else market
            _price = rate if rate else STRING_UNAVAILABLE
            _symbol = self.currency_map.get(market[-3:], market[-3:])
            _symbol = _symbol if self.symbols else market

            rates.append(
                self.py3.safe_format(
                    self.format_bitcoin,
                    {"market": _market, "price": _price, "symbol": _symbol},
                )
            )

        # colorize if an index is given or only one market is selected
        if len(rates) == 1 or self.color_index > -1:
            if self.last_price == 0:
                pass
            elif color_rate < self.last_price:
                response["color"] = self.py3.COLOR_BAD
            elif color_rate > self.last_price:
                response["color"] = self.py3.COLOR_GOOD
            self.last_price = color_rate

        format_separator = self.py3.safe_format(self.format_separator)
        format_bitcoin = self.py3.composite_join(format_separator, rates)
        response["full_text"] = self.py3.safe_format(
            self.format, {"format_bitcoin": format_bitcoin}
        )
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
