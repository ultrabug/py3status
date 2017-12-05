# -*- coding: utf-8 -*-
"""
Display cryptocurrency data.

The site we retrieve cryptocurrency data from offer various types of data such as
name, symbol, price, volume, percentage change, total supply, et cetera for a wide
range of cryptocurrencies and the prices can be obtained in a different currency
along with USD currency, For more information, visit https://coinmarketcap.com

Configuration parameters:
    cache_timeout: refresh interval for this module. A message from the site:
        Please limit requests to no more than 10 per minute. (default 600)
    format: display format for this module (default '{format_coin}')
    format_coin: display format for coins
        (default '{name} ${price_usd:.2f} [\?color=24h {percent_change_24h}%]')
    format_separator: show separator if more than one (default ' ')
    markets: number of top-ranked markets or list of user-inputted markets
        (default ['btc'])
    request_timeout: time to wait for a response, in seconds (default 5)
    thresholds: for percentage changes (default [(-100, 'bad'), (0, 'good')])

Format placeholder:
    {format_coin} format for cryptocurrency coins

format_coin placeholders:
    {24h_volume_usd}      eg 1435150000.0
    {available_supply}    eg 16404825.0
    {id}                  eg bitcoin
    {last_updated}        eg 1498135152
    {market_cap_usd}      eg 44119956596.0
    {name}                eg Bitcoin
    {percent_change_1h}   eg -0.17
    {percent_change_24h}  eg -1.93
    {percent_change_7d}   eg +14.73
    {price_btc}           eg 1.0
    {price_usd}           eg 2689.45
    {rank}                eg 1
    {symbol}              eg BTC
    {total_supply}        eg 16404825.0

    Placeholders are retrieved directly from the URL.
    The list was harvested only once and should not represent a full list.

    To print coins in different currency, replace or replicate the placeholders
    below with a valid option (eg '{price_gbp}') to create additional placeholders:

    {price_xxx}           eg (new output here)
    {24h_volume_xxx}      eg (new output here)
    {market_cap_xxx}      eg (new output here)

    Valid options are: AUD, BRL, CAD, CHF, CNY, EUR, GBP, HKD, IDR, INR,
    JPY, KRW, MXN, RUB, otherwise USD... and be written in lowercase.

Color thresholds:
    1h:  print color based on the value of percent_change_1h
    24h: print color based on the value of percent_change_24h
    7d:  print color based on the value of percent_change_7d

Example:
```
# view coins in GBP and optionally USD
coin_market {
    format_coin = '{name} £{price_gbp:.2f} ${price_usd:.2f} {percent_change_24h}'
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


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 600
    format = '{format_coin}'
    format_coin = '{name} ${price_usd:.2f} [\?color=24h {percent_change_24h}%]'
    format_separator = ' '
    markets = ['btc']
    request_timeout = 5
    thresholds = [(-100, 'bad'), (0, 'good')]

    def post_config_hook(self):
        self.first_run = self.first_use = True
        self.convert = self.limit = None
        self.url = self.reset_url = 'https://api.coinmarketcap.com/v1/ticker/'

        # find out if we want top-ranked markets or user-inputted markets
        if isinstance(self.markets, int):
            self.limit = self.markets
        else:
            self.markets = [x.upper().strip() for x in self.markets]

        # create '?convert'
        for item in self.py3.get_placeholders_list(self.format_coin):
            if (('price' in item and 'price_btc' not in item) or
                    '24h_volume' in item or 'market_cap' in item) \
                    and 'usd' not in item:
                self.convert = '?convert=%s' % (item.split('_')[-1])
                self.url = self.reset_url = self.reset_url + self.convert
                break

        # create '(?|&)limit'
        if self.limit:
            self._update_limit(None)

    def _get_coin_data(self, reset=False):
        if reset:
            self.url = self.reset_url
        try:
            data = self.py3.request(self.url, timeout=self.request_timeout).json()
        except self.py3.RequestException:
            data = {}
        return data

    def _update_limit(self, data):
        # we use limit if it exists. otherwise, we stretch the limit
        # large enough to obtain (all) self.markets + some padding
        self.url = self.url + ('&' if self.convert else '?')
        if self.limit:
            limit = self.limit
        else:
            limit = 0
            for market_id in self.markets:
                index = next((i for (i, d) in enumerate(
                    data) if d['symbol'] == market_id), -1)
                if index >= limit:
                    limit = index
                    limit += 5  # padding

        self.url += 'limit=%s' % limit

    def _strip_data(self, data):
        # if self.limit, we don't strip. otherwise, we strip 1000+ coins
        # down to %s coins by removing everything not in self.markets.
        new_data = []
        if self.limit:
            new_data = data
        else:
            for symbol in self.markets:
                for market in data:
                    if symbol == market['symbol']:
                        new_data.append(market)
                        break

        return new_data

    def _organize_data(self, data):
        # compare len(stripped(1000+ coins) with len(self.markets)
        new_data = self._strip_data(data)
        is_equal = len(new_data) == len(self.markets)

        # first_use bad? the user entered bad markets. stop here (error).
        # otherwise, make a limit for first time on 1000+ coins.
        if self.first_use:
            self.first_use = False
            if not is_equal:
                self.py3.error('bad markets')
            else:
                self._update_limit(data)
        elif not is_equal:
            # post first_use bad? the markets fell out of the limit + padding.
            # reset the url to get 1000+ coins again so we can strip, compare,
            # make new limit + padding for next loop, but we'll use that new
            # data. otherwise, we would keep going with that first new_data.
            new_data = self._get_coin_data(reset=True)
            new_data = self._strip_data(new_data)
            self._update_limit(new_data)

        return new_data

    def _manipulate_data(self, data):
        # we mess with raw data to get the new results. we fix up percent_change
        # with color thresholds and prefix all non-negative values wth a plus.
        new_data = []
        for market in data:
            temporary = {}
            for k, v in market.items():
                if 'percent_change_' in k and v:
                    temporary[k] = '+%s' % v if float(v) > 0 else v
                    # remove 'percent_change_' for thresholds: 1h, 24h, or 7d
                    self.py3.threshold_get_color(v, k[15:])
                else:
                    temporary[k] = v

            new_data.append(self.py3.safe_format(self.format_coin, temporary))

        return new_data

    def coin_market(self):
        data = []
        if self.first_run:
            self.first_run = False
            cached_until = 0
        else:
            # first 1000+ coins (then %s coins)
            cached_until = self.cache_timeout
            coin_data = self._get_coin_data()
            if not self.limit:
                # strip, compare, and maybe update again
                coin_data = self._organize_data(coin_data)
            data = self._manipulate_data(coin_data)  # paint coin colors

        format_separator = self.py3.safe_format(self.format_separator)
        format_coin = self.py3.composite_join(format_separator, data)

        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(self.format, {'format_coin': format_coin})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
