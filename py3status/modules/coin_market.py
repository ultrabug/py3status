# -*- coding: utf-8 -*-
"""
Display cryptocurrency data.

Configuration parameters:
    cache_timeout: refresh interval for this module. A message from the site:
        Please limit requests to no more than 10 per minute.
        (default 600)
    format: display format for this module (default '{format_coin}')
    format_coin: display format for coins
        (default '[\?color=degraded {name}] ${price_usd:.2f} {percent_change_24h}')
    format_separator: show separator only if more than one (default ' ')
    markets: comma separated list of supported markets https://coinmarketcap.com
        (default ['btc'])
    request_timeout: time to wait for a response, in seconds (default 5)

Format placeholder:
    {format_coin} format for cryptocurrency coins

format_coin placeholders:
    {24h_volume_usd}      eg 1435150000.0
    {available_supply}    eg 16404825.0
    {id}                  eg bitcoin
    {last_updated}        eg 1498135152
    {market_cap_usd}      eg 44119956596.0
    {name}                eg Bitcoin
    {percent_change_1h}   eg -0.17%
    {percent_change_24h}  eg -1.93%
    {percent_change_7d}   eg +14.73%
    {price_btc}           eg 1.0
    {price_usd}           eg 2689.45
    {rank}                eg 1
    {symbol}              eg BTC
    {total_supply}        eg 16404825.0

    Placeholders are retrieved directly from the URL.
    The list was harvested only once and should not represent a full list.

    To view placeholders in different currency, replace `_usd` with a valid option
    (eg '{price_usd}' to '{price_xxx}'). Case insensitive. Valid options are: AUD,
    BRL, CAD, CHF, CNY, EUR, GBP, HKD, IDR, INR, JPY, KRW, MXN, RUB, otherwise USD.

@author x86kernel, lasers

SAMPLE OUTPUT
[
    {'color': u'#FFFF00', 'full_text': u'Bitcoin'},
    {'full_text': u' $2735.77 '},
    {'color': '#00FF00', 'full_text': u'+2.27%'},
]

losers
[
    {'color': u'#FFFF00', 'full_text': u'Bitcoin'},
    {'full_text': u' $2701.70 '},
    {'color': '#FF0000', 'full_text': u'-0.42%'},
]
"""


class Py3status:
    cache_timeout = 600
    format = '{format_coin}'
    format_coin = '[\?color=degraded {name}] ${price_usd:.2f} {percent_change_24h}'
    format_separator = ' '
    markets = ['btc']
    request_timeout = 5

    def post_config_hook(self):
        self.first = True
        if not isinstance(self.markets, list):
            self.markets = self.markets.split(',')
        self.markets = [x.upper().strip() for x in self.markets]
        self.url = 'https://api.coinmarketcap.com/v1/ticker/?convert=%s'
        for item in self.py3.get_placeholders_list(self.format_coin):
            if '24h_volume_' in item or 'market_cap_' in item or (
                    'price_' in item and 'price_btc' not in item):
                self.url = self.url % (item.split('_')[-1])
                break

        self.coin_data = self._get_coin_data()
        limit = 0
        for market_id in self.markets:
            index = next((i for (
                i, d) in enumerate(self.coin_data) if d['symbol'] == market_id), -1)
            if index > limit:
                limit = index
        self.url = self.url + '&limit=%s' % (limit + 1)

    def _get_coin_data(self):
        try:
            data = self.py3.request(self.url, timeout=self.request_timeout).json()
        except self.py3.RequestException:
            data = {}
        return data

    def coin_market(self):
        data = []
        if not self.first:
            self.coin_data = self._get_coin_data()
        else:
            self.first = False

        if self.coin_data:
            for market_id in self.markets:
                for currency in self.coin_data:
                    if market_id == currency['symbol']:
                        market = currency
                        break

                temporary = {}
                for k, v in market.items():
                    if 'percent_change' in k and v:
                        if float(v) >= 0:
                            _fmt = '\?color=%s %s' % ('good', v)
                        else:
                            _fmt = '\?color=%s %s' % ('bad', v)
                        _fmt = '+' + _fmt if float(v) > 0 else _fmt
                        temporary[k] = self.py3.safe_format(_fmt + '%')
                    else:
                        temporary[k] = v

                data.append(self.py3.safe_format(self.format_coin, temporary))

        format_separator = self.py3.safe_format(self.format_separator)
        format_coin = self.py3.composite_join(format_separator, data)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'format_coin': format_coin})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
