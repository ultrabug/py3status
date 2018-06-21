# -*- coding: utf-8 -*-
"""
Display cryptocurrency markets.

The site offer various types of data such as symbol, trades, volumes,
weighted prices, et cetera for a wide range of cryptocurrency markets.
For more information, visit https://bitcoincharts.com

Configuration parameters:
    cache_timeout: refresh interval for this module. a message from the site:
        don't query more often than once every 15 minutes (default 900)
    format: display format for this module (default '{format_market}')
    format_market: display format for cryptocurrency markets
        *(default '{symbol} {currency_symbol}{close:.2f} '
        '[\?color=close_change {close_sign}{close_change:.2f}%]')*
    format_separator: show separator if more than one (default ' ')
    markets: specify a list of active/inactive markets to use,
        see https://bitcoincharts.com/markets/list (default ['bitstampUSD'])
    thresholds: specify color thresholds to use
        (default [(-1, 'bad'), (0, 'good')])

Format placeholders:
    {format_market} format for cryptocurrency markets
    {xxx_24h}       weighted price for last 24 hours eg 1234.56
    {xxx_7d}        weighted price for last  7 days eg 1234.56
    {xxx_30d}       weighted price for last 30 days eg 1234.56
  * {xxx_sign}      sign change between intervals, eg '', +, -
  * {xxx_change}    percent change between intervals, eg 0.123456
  * {xxx_diff}      actual difference between intervals, eg 33.56

    The symbol `*` denotes custom and is not part of Bitcoincharts.
    Replace xxx with options below.

    Bitcoincharts offers weighted prices for several currencies.
    Weighted prices are calculated for the last 24 hours, 7 days and 30 days.
    You can use this to price goods and services in Bitcoins. This will yield
    much lower fluctuations than using a single market's latest price.

    To print weighted prices in different currency, replicate the placeholders
    with a valid option, eg `{usd_24h}`. You can use many as you like.

    Valid options are: ARS, AUD, BRL, CAD, CHF, CLP, CZK, DKK, EUR, GBP, HKD,
    IDR, ILS, INR, JPY, KRW, MXN, MYR, NGN, NOK, NZD, PKR, PLN, RUB, SEK, SGD,
    SLL, THB, USD, VEF, VND, ZAR... and be written in lowercase.

format_market placeholders:
    {symbol}          symbol name, eg bitstampUSD
    {currency}        currency, eg USD, EUR, GBP
    {bid}             highest bid price, eg 1704347.14
    {ask}             lowest ask price, eg 12100.0,
    {avg}             average price, eg 17265.00867749991
    {latest_trade}    unixtime of latest trade, eg 1513072778
    {high}            highest trade during day, eg 68874.32
    {low}             lowest trade during day, eg 11401.79
    {close}           latest trade, eg 24183.56
    {volume}          total trade volume of day in BTC, eg 143.11342831
    {currency_volume} total trade volume of day in currency, eg 2470854.581638
    {weighted_price}  weighted price for this day eg 17265.00867749991
    {duration}        duration, eg 89282
  * {currency_symbol} currency symbol, eg $, €, £
  * {xxx_sign}        sign change between intervals, eg '', +, -
  * {xxx_change}      percent change between intervals, eg 0.123456
  * {xxx_diff}        actual difference between intervals, eg 33.56

    The symbol `*` denotes custom is not part of Bitcoincharts.
    Replace xxx with placeholders above.

Color options:
    color_bad: the price has dropped since the last interval
    color_good: the price hasn't changed or increased since the last interval

Color thresholds:
    format:
        xxx:        print a color based on the value of `xxx` placeholder
        xxx_change: print a color based on percent change between intervals
        xxx_diff:   print a color based on the value of `xxx_diff` placeholder
    format_market:
        xxx:        print a color based on the value of `xxx` placeholder
        xxx_change: print a color based on percent change between intervals
        xxx_diff:   print a color based on the value of `xxx_diff` placeholder

Examples:
```
# add more markets
bitcoin_charts {
    markets = ['bitstampUSD', 'coinbaseUSD', 'localbtcUSD']
}

# colorize usd_24h weighted prices
bitcoin_charts {
    format = '[\?color=gold&show MARKET][ {format_market} ]'
    format += '[\?color=gold&show USD_24H][ ${usd_24h} '
    format += '[\?color=usd_24h_change {usd_24h_sign}${usd_24h_diff}], '
    format += '[\?color=usd_24h_change {usd_24h_sign}{usd_24h_change}%]]'

    # i believe this switches over at around 7:00 AM UTC so it should be the
    # only time you can catch this in action between dailys, otherwise it will
    # be same and unchanged until the next day. this format shows everything
    # you can use with one {usd_24h} placeholder.
}

# round to the nearest whole number
bitcoin_charts {
    format_market = '{symbol} [\?color=close_change {currency_symbol}{close:.0f}]'
}

# remove last 3 letters, eg USD, from symbol, formatter hack
bitcoin_charts {
    format_market = '[\?max_length=-3 {symbol}] '
    format_market += '[\?color=close_change {currency_symbol}{close:.2f}]'
}

# display differences between intervals, eg sign, change, diff
bitcoin_charts {
    format_market = '{symbol} {currency_symbol}{close:.2f} '
    format_market += '[\?color=close_change {close_sign}{currency_symbol}{close_diff}], '
    format_market += '[\?color=close_change {close_sign}{close_change}%]'

    # it is easier to use $. otherwise, it is useful to use {currency_symbol}
    # if you're planning on using mixed {currency} markets in your format
}

# colorize degraded on zeroes or zero differences
bitcoin_charts {
    thresholds = [(-1, 'bad'), (0, 'degraded'), (0.001, 'good')]
    # you may like darkgray or other dark color better
}
```

@author Andre Doser <doser.andre AT gmail.com>, lasers

SAMPLE OUTPUT
[
    {'full_text': 'bitstampUSD $9471.52 '},
    {'full_text': '-1.18%', 'color': '#ff0000'},
    {'full_text': 'localbtcUSD $9700.00 '},
    {'full_text': '+1.39%', 'color': '#00ff00'},
]
"""
URL = 'https://api.bitcoincharts.com/v1/{}.json'
MAP = {'AUD': '$', 'CNY': '¥', 'EUR': '€', 'GBP': '£', 'USD': '$', 'YEN': '¥'}


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 900
    format = '{format_market}'
    format_market = (
        '{symbol} {currency_symbol}{close:.2f} '
        '[\?color=close_change {close_sign}{close_change:.2f}%]')
    format_separator = ' '
    markets = ['bitstampUSD']
    thresholds = [(-1, 'bad'), (0, 'good')]

    class Meta:
        update_config = {
            'update_placeholder_format': [
                {
                    'placeholder_formats': {
                        'price': ':.2f',
                    },
                    'format_strings': ['format_bitcoin'],
                }
            ],
        }

        def deprecate_function(config):
            if (not config.get('format_separator') and
                    config.get('bitcoin_separator')):
                sep = config.get('bitcoin_separator')
                sep = sep.replace('\\', '\\\\')
                sep = sep.replace('[', '\[')
                sep = sep.replace(']', '\]')
                sep = sep.replace('|', '\|')

                return {'format_separator': sep}
            else:
                return {}

        deprecated = {
            'function': [
                {
                    'function': deprecate_function,
                },
            ],
            'remove': [
                {
                    'param': 'bitcoin_separator',
                    'msg': 'obsolete set using `format_separator`',
                },
                {
                    'param': 'hide_on_error',
                    'msg': 'obsolete parameter',
                },
                {
                    'param': 'color_index',
                    'msg': 'obsolete parameter',
                },
            ],
            'rename': [
                {
                    'param': 'format_bitcoin',
                    'new': 'format_market',
                    'msg': 'obsolete parameter use `format_market`',
                },
            ],
            'rename_placeholder': [
                {
                    'placeholder': 'format_bitcoin',
                    'new': 'format_market',
                    'format_strings': ['format'],
                },
            ],
        }

    def post_config_hook(self):
        # deprecation
        if not isinstance(self.markets, list):
            self.markets = [x.strip() for x in self.markets.split(',')]
        self.field = getattr(self, 'field', 'close')
        self.symbols = getattr(self, 'symbols', True)
        self.price = self.py3.format_contains(self.format_market, 'price*')

        # init
        self.diff_keys = ['_sign', '_change', '_diff', '_change_', '_diff_']
        self.init = {}
        self.request_timeout = 10
        self.thresholds_init = {}
        init_policies = [  # names, format_string, matched
            ('markets', self.format_market, None),
            ('weighted_prices', self.format, ['*_24h*', '*_30d*', '*_7d*'])
        ]

        # init methods + placeholders for markets and weighted_prices
        for x in init_policies:
            matched_placeholders = self.py3.get_placeholders_list(x[1], x[2])
            new_list = []
            # add example instead of example_change, example_diff
            for name in matched_placeholders:
                for partial in self.diff_keys:
                    if name.endswith(partial):
                        new_list.append(name.split(partial)[0])
                        break
                else:
                    new_list.append(name)
            self.init[x[0]] = list(set(new_list))
        if not self.py3.format_contains(self.format, 'format_market'):
            self.init['markets'] = []
        self.init['methods'] = [k for k, v in self.init.items() if v]

        # partial future helper code
        for name in ('format', 'format_market'):
            self.thresholds_init[name] = []
            for x in getattr(self, name).replace('&', ' ').split('color=')[1::1]:
                self.thresholds_init[name].append(x.split()[0])

    def _get_data(self, name):
        try:
            data = self.py3.request(
                URL.format(name), timeout=self.request_timeout).json()
        except self.py3.RequestException:
            data = {}
        return data

    def _manipulate_markets(self, data):
        new_market = []
        for name in self.markets:
            for market in data:
                # skip nonmatched markets
                if name != market['symbol']:
                    continue
                sign = market['currency']
                market['currency_symbol'] = MAP.get(sign, sign)

                # deprecation: show field->price + market==symbol
                _market = market['symbol']
                if self.price:
                    market['symbol'] = market['currency_symbol']
                    if self.field in market:
                        market['price'] = market[self.field]
                market['market'] = _market[:-3] if self.symbols else _market
                # end deprecation

                for key in self.init['markets']:
                    try:
                        value = float(market[key])
                    except (KeyError, TypeError, ValueError):
                        continue
                    market.update(dict(zip(
                        [key + x for x in self.diff_keys],
                        self.py3.format_diffs(key, value, name)
                    )))

                for x in self.thresholds_init['format_market']:
                    if '_change' in x or '_diff' in x:
                        y = x + '_'
                        if y in market:
                            self.py3.threshold_get_color(market[y], x)
                    elif x in market:
                        self.py3.threshold_get_color(market[x], x)

                new_market.append(
                    self.py3.safe_format(self.format_market, market)
                )
                break

        format_separator = self.py3.safe_format(self.format_separator)
        format_market = self.py3.composite_join(format_separator, new_market)
        data = {'format_market': format_market}

        return data

    def _manipulate_weighted_prices(self, data):
        data = {k.lower(): v for k, v in data.items()}
        data = self.py3.flatten_dict(data, '_')
        for key in self.init['weighted_prices']:
            try:
                value = float(data[key])
            except (KeyError, TypeError, ValueError):
                continue
            data.update(dict(zip(
                [key + x for x in self.diff_keys],
                self.py3.format_diffs(key, value, 'weighted_prices')
            )))

        for x in self.thresholds_init['format']:
            if '_change' in x or '_diff' in x:
                y = x + '_'
                if y in data:
                    self.py3.threshold_get_color(data[y], x)
            elif x in data:
                self.py3.threshold_get_color(data[x], x)

        return data

    def bitcoin_charts(self):
        charts_data = {}
        for name in self.init['methods']:
            charts_data.update(
                getattr(self, '_manipulate_' + name)(self._get_data(name))
            )

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, charts_data),
        }


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
