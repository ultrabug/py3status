# -*- coding: utf-8 -*-
"""
Display cryptocurrency coins.

The site offer various types of data such as name, symbol, price, volume,
total supply, et cetera for a wide range of cryptocurrencies and the prices
can be obtained in a different currency along with optional USD currency.
For more information, visit https://coinmarketcap.com

Configuration parameters:
    cache_timeout: refresh interval for this module. a message from the site:
        please limit requests to no more than 10 per minute. (default 600)
    format: display format for this module (default '{format_coin}')
    format_coin: display format for coins
        *(default '{name} ${price_usd:.2f} '
        '[\?color=percent_change_24h {percent_change_24h}%]')*
    format_datetime: specify strftime characters to format (default {})
    format_separator: show separator if more than one (default ' ')
    markets: number of top-ranked markets or list of user-inputted markets
        (default ['btc'])
    thresholds: specify color thresholds to use
        (default [(-100, 'bad'), (0, 'good')])

Format placeholders:
    {format_coin} format for cryptocurrency coins

format_datetime placeholders:
    key: epoch_placeholder, eg last_updated
    value: % strftime characters to be translated, eg '%b %d' ----> 'Nov 29'

format_coin placeholders:
    {id}                 eg bitcoin
    {name}               eg Bitcoin
    {symbol}             eg BTC
    {rank}               eg 1
    {price_usd}          eg 11163.4
    {price_btc}          eg 1.0
    {24h_volume_usd}     eg 10156700000.0
    {market_cap_usd}     eg 186528134260
    {available_supply}   eg 16708900.0
    {total_supply}       eg 16708900.0
    {max_supply}         eg 21000000.0
    {percent_change_1h}  eg 0.92
    {percent_change_24h} eg 11.2
    {percent_change_7d}  eg 35.96
    {last_updated}       eg 151197295

    Placeholders are retrieved directly from the URL.
    The list was harvested once and should not represent a full list.

    To print coins in different currency, replace or replicate the placeholders
    below with a valid option (eg '{price_gbp}') to create additional placeholders:

    {price_xxx}           eg (new output here)
    {24h_volume_xxx}      eg (new output here)
    {market_cap_xxx}      eg (new output here)

    Valid options are: AUD, BRL, CAD, CHF, CNY, EUR, GBP, HKD, IDR, INR,
    JPY, KRW, MXN, RUB, otherwise USD... and be written in lowercase.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Examples:
```
# view coins in GBP and optionally USD
coin_market {
    format_coin = '{name} £{price_gbp:.2f} ${price_usd:.2f} {percent_change_24h}'
}

# display top five markets
coin_market {
    markets = 5
}

# colorize market names
coin_market {
    format_coin = "[\?color=name {name}] ${price_usd:.2f} "
    format_coin += "[\?color=percent_change_24h {percent_change_24h}%]"
    markets = ["btc", "eth", "ltc", "doge"]
    thresholds = {
        "name": [
            ("Bitcoin", "greenyellow"),
            ("Ethereum", "deepskyblue"),
            ("Litecoin", "crimson"),
            ("Dogecoin", "orange"),
        ],
        "percent_change_24h": [(-100, "bad"), (0, "good")],
    }
}

# show and/or customize last_updated time
coin_market {
    format_coin = '{name} ${price_usd:.2f} '
    format_coin += '[\?color=percent_change_24h {percent_change_24h}%] {last_updated}'
    format_datetime = {'last_updated': '\?color=degraded last updated %-I:%M%P'}
}
```

@author lasers, x86kernel

SAMPLE OUTPUT
[
    {'color': '#FFFFFF', 'full_text': 'Bitcoin $2735.77 '},
    {'color': '#00FF00', 'full_text': '+2.27%'},
]

losers
[
    {'color': '#FFFFFF', 'full_text': 'Bitcoin $2701.70 '},
    {'color': '#FF0000', 'full_text': '-0.42%'},
]
"""

from datetime import datetime


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 600
    format = "{format_coin}"
    format_coin = (
        "{name} ${price_usd:.2f} [\?color=percent_change_24h {percent_change_24h}%]"
    )
    format_datetime = {}
    format_separator = " "
    markets = ["btc"]
    thresholds = [(-100, "bad"), (0, "good")]

    def post_config_hook(self):
        self.first_use = True
        self.convert = self.limit = None
        self.url = self.reset_url = "https://api.coinmarketcap.com/v1/ticker/"

        # convert the datetime?
        self.init_datetimes = []
        for word in self.format_datetime:
            if (self.py3.format_contains(self.format_coin, word)) and (
                word in self.format_datetime
            ):
                self.init_datetimes.append(word)

        # find out if we want top-ranked markets or user-inputted markets
        if isinstance(self.markets, int):
            self.limit = self.markets
        else:
            self.markets = [x.upper().strip() for x in self.markets]

        # create '?convert'
        placeholders = self.py3.get_placeholders_list(self.format_coin)
        for item in placeholders:
            if (
                ("price" in item and "price_btc" not in item)
                or "24h_volume" in item
                or "market_cap" in item
            ) and "usd" not in item:
                self.convert = "?convert=%s" % (item.split("_")[-1])
                self.url = self.reset_url = self.reset_url + self.convert
                break

        # create '(?|&)limit'
        if self.limit:
            self._update_limit(None)

        # thresholds
        percents = {x: "percent_change_" + x for x in ["1h", "24h", "7d"]}
        self.thresholds_init = {
            "percents": percents,
            "format_coin": self.py3.get_color_names_list(self.format_coin),
            "plus": [x for x in placeholders if x in percents.values()],
        }

    def _get_coin_data(self, reset=False):
        if reset:
            self.url = self.reset_url
        try:
            data = self.py3.request(self.url).json()
        except self.py3.RequestException:
            data = {}
        return data

    def _update_limit(self, data):
        # we use limit if it exists. otherwise, we stretch the limit
        # large enough to obtain (all) self.markets + some padding
        self.url = self.url + ("&" if self.convert else "?")
        if self.limit:
            limit = self.limit
        else:
            limit = 0
            for market_id in self.markets:
                index = next(
                    (i for (i, d) in enumerate(data) if d["symbol"] == market_id), -1
                )
                if index >= limit:
                    limit = index
                    limit += 5  # padding

        self.url += "limit=%s" % limit

    def _strip_data(self, data):
        # if self.limit, we don't strip. otherwise, we strip 1000+ coins
        # down to %s coins by removing everything not in self.markets.
        new_data = []
        if self.limit:
            new_data = data
        else:
            for symbol in self.markets:
                for market in data:
                    if symbol == market["symbol"]:
                        new_data.append(market)
                        break

        return new_data

    def _organize_data(self, data):
        # compare len(stripped(1000+ coins) with len(self.markets)
        new_data = self._strip_data(data)
        is_equal = len(new_data) == len(self.markets)

        # first_use bad? the user entered bad markets. stop here (error).
        # otherwise, make a limit for first time on 1000+ coins.
        if data and self.first_use:
            self.first_use = False
            if not is_equal:
                self.py3.error("bad markets")
            else:
                self._update_limit(data)
        elif not is_equal:
            # post first_use bad? the markets fell out of the limit + padding.
            # reset the url to get 1000+ coins again to strip, compare, make
            # new limit and padding for the next one, but we'll use this one.
            # otherwise, we would have kept going with the first one.
            new_data = self._get_coin_data(reset=True)
            new_data = self._strip_data(new_data)
            self._update_limit(new_data)

        return new_data

    def _manipulate_data(self, data):
        new_data = []
        for market in data:
            # datetimes
            for k in self.init_datetimes:
                if k in market:
                    market[k] = self.py3.safe_format(
                        datetime.strftime(
                            datetime.fromtimestamp(float(market[k])),
                            self.format_datetime[k],
                        )
                    )
            # thresholds
            for x in self.thresholds_init["format_coin"]:
                if x in market:
                    self.py3.threshold_get_color(market[x], x)
                elif x in self.thresholds_init["percents"]:
                    y = self.thresholds_init["percents"][x]
                    self.py3.threshold_get_color(market[y], x)

            # prefix non-negative percents with a plus.
            for x in self.thresholds_init["plus"]:
                if float(market[x]) > 0:
                    market[x] = "+{}".format(market[x])

            new_data.append(self.py3.safe_format(self.format_coin, market))

        return new_data

    def coin_market(self):
        # first 1000+ coins (then %s coins)
        coin_data = self._get_coin_data()
        if not self.limit:
            # strip, compare, and maybe update again
            coin_data = self._organize_data(coin_data)
        data = self._manipulate_data(coin_data)

        format_separator = self.py3.safe_format(self.format_separator)
        format_coin = self.py3.composite_join(format_separator, data)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format, {"format_coin": format_coin}
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
