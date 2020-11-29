r"""
Display cryptocurrency coins.

The site offer various types of data such as name, symbol, price, volume, total
supply, et cetera for a wide range of cryptocurrencies in various currencies.
For more information, visit https://coinmarketcap.com

Configuration parameters:
    api_key: specify CoinMarketCap api key (default None)
    cache_timeout: refresh interval for this module. a message from the site:
        please limit requests to no more than 30 calls per minute. (default 600)
    format: display format for this module (default '{format_coin}')
    format_coin: display format for coins
        *(default '{name} ${usd_price:.2f} '
        '[\?color=usd_percent_change_24h {usd_percent_change_24h:.1f}%]')*
    format_coin_separator: show separator if more than one (default ' ')
    markets: specify a list of markets (default ['btc', 'eth'])
    thresholds: specify color thresholds to use
        (default [(-100, 'bad'), (0, 'good')])

Format placeholders:
    {format_coin} format for cryptocurrency coins

format_coin placeholders:
    {circulating_supply}     eg 17906012
    {cmc_rank}               eg 1
    {date_added}             eg 2013-04-28T00:00:00.000Z
    {id}                     eg 1
    {is_active}              eg 1
    {is_fiat}                eg 0
    {is_market_cap_included_in_calc} eg 1
    {last_updated}           eg 2019-08-30T18:51:28.000Z
    {max_supply}             eg 21000000
    {name}                   eg Bitcoin
    {num_market_pairs}       eg 7919
    {platform}               eg None
    {slug}                   eg bitcoin
    {symbol}                 eg BTC
    {tags}                   eg ['mineable']
    {total_supply}           eg 17906012

    Placeholders are retrieved directly from the URL.
    The list was harvested once and should not represent a full list.

    To print coins in different currencies, replicate the placeholders
    below with valid options (eg '{gbp_price:.2f}'):

    {xxx_last_updated}       eg 2019-08-30T18:51:28.000Z'
    {xxx_market_cap}         eg 171155540318.86005
    {xxx_percent_change_1h}  eg -0.127291
    {xxx_percent_change_24h} eg 0.328918
    {xxx_percent_change_7d}  eg -8.00576
    {xxx_price}              eg 9558.55163723
    {xxx_volume_24h}         eg 13728947008.2722

    See https://coinmarketcap.com/api/documentation/v1/#section/Standards-and-Conventions
    for valid options, otherwise USD... in lowercase.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Examples:
```
# view coins in GBP and EUR
coin_market {
    format_coin = "{name} £{gbp_price:.2f} €{eur_price:.2f}"
}

# colorize market names + symbols
coin_market {
    format_coin = "[\?color=name {name}] "
    format_coin += "[\?color=symbol {symbol}] ${usd_price:.2f} "
    format_coin += "[\?color=usd_percent_change_24h {usd_percent_change_24h}%]"
    markets = ["btc", "eth", "ltc", "doge"]
    thresholds = {
        "name": [
            ("Bitcoin", "greenyellow"),
            ("Ethereum", "deepskyblue"),
            ("Litecoin", "crimson"),
            ("Dogecoin", "orange"),
        ],
        "symbol": [
            ("BTC", "darkgray"),
            ("ETH", "darkgray"),
            ("LTC", "darkgray"),
            ("DOGE", "darkgray"),
        ],
        "usd_percent_change_24h": [(-100, "bad"), (0, "good")],
    }
}
```

@author lasers, x86kernel

SAMPLE OUTPUT
[
    {'color': '#FFFFFF', 'full_text': 'Bitcoin $2735.77 '},
    {'color': '#00FF00', 'full_text': '2.27%'},
]

losers
[
    {'color': '#FFFFFF', 'full_text': 'Bitcoin $2701.70 '},
    {'color': '#FF0000', 'full_text': '-0.42%'},
]
"""

INVALID_API_KEY = "invalid api_key"


class Py3status:
    """"""

    # available configuration parameters
    api_key = None
    cache_timeout = 600
    format = "{format_coin}"
    format_coin = r"{name} ${usd_price:.2f} [\?color=usd_percent_change_24h {usd_percent_change_24h:.1f}%]"
    format_coin_separator = " "
    markets = ["btc", "eth"]
    thresholds = [(-100, "bad"), (0, "good")]

    def post_config_hook(self):
        if not self.api_key:
            self.py3.error(INVALID_API_KEY)

        currency_options = [
            "_last_updated",
            "_market_cap",
            "_percent_change_1h",
            "_percent_change_24h",
            "_percent_change_7d",
            "_price",
            "_volume_24h",
        ]

        convert = set()
        for item in self.py3.get_placeholders_list(self.format_coin):
            if item[3:].endswith(tuple(currency_options)):
                convert.add(item.split("_", 1)[0])
        convert, markets = ",".join(convert), ",".join(self.markets)

        self.headers = {
            "Accepts": "applications/json",
            "X-CMC_PRO_API_KEY": self.api_key,
        }
        self.url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes"
        self.url += f"/latest?convert={convert}&symbol={markets}"

        self.thresholds_init = self.py3.get_color_names_list(self.format_coin)

    def _get_coin_data(self):
        try:
            cmc_data = self.py3.request(self.url, headers=self.headers).json()
            data = []

            for name, currency_data in cmc_data.get("data", {}).items():
                quotes = currency_data.pop("quote", {})
                quotes = {k.lower(): v for k, v in quotes.items()}
                currency_data.update(self.py3.flatten_dict(quotes, delimiter="_"))
                data.append(currency_data)

        except self.py3.RequestException:
            data = []
        return data

    def coin_market(self):
        coin_data = self._get_coin_data()
        new_coin = []

        for market in coin_data:
            for x in self.thresholds_init:
                if x in market:
                    self.py3.threshold_get_color(market[x], x)

            new_coin.append(self.py3.safe_format(self.format_coin, market))

        format_coin_separator = self.py3.safe_format(self.format_coin_separator)
        format_coin = self.py3.composite_join(format_coin_separator, new_coin)

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
