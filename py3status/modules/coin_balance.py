# -*- coding: utf-8 -*-
"""
Display balances of diverse crypto-currencies.

This module grabs your current balance of different crypto-currents from a
wallet server. The server must conform to the bitcoin RPC specification.
Currently Bitcoin, Dogecoin, and Litecoin are supported.

Configuration parameters:
    cache_timeout: An integer specifying the cache life-time of the output in
        seconds (default 30)
    coin_password: A string containing the password for the server for
        'coin'. The 'coin' part must be replaced by a supported coin identifier
        (see below for a list of identifiers). If no value is supplied,
        the value of 'password' (see below) will be used.  If 'password' too is
        not set, the value will be retrieved from the standard 'coin' daemon
        configuration file. (default None)
    coin_username: A string containing the username for the server for
        'coin'. The 'coin' part must be replaced by a supported coin identifier
        (see below for a list of identifiers). If no value is supplied,
        the value of 'username' (see below) will be used.  If 'username' too is
        not set, the value will be retrieved from the standard 'coin' daemon
        configuration file. (default None)
    credentials: (default None)
    format: A string describing the output format for the module. The {<coin>}
        placeholder (see below) will be used to determine how to fetch the
        coin balance. Multiple placeholders are allowed, but all balances will
        be fetched from the same host. (default 'LTC: {litecoin}')
    host: The coin-server hostname. Note that all coins will use the same host
        for their querries. (default 'localhost')
    password: A string containing the password for all coin-servers. If neither
        this setting, nor a specific coin_password (see above) is specified,
        the password for each coin will be read from the respective standard
        daemon configuration file. (default None)
    protocol: A string to select the server communication protocol.
        (default 'http')
    username: A string containing the username for all coin-servers. If neither
        this setting, nor a specific coin_username (see above) is specified,
        the username for each coin will be read from the respective standard
        daemon configuration file. (default None)

Format placeholders:
    {<coin>} Your balance for the coin <coin> where <coin> is one of:
        - bitcoin
        - dogecoin
        - litecoin

Requires:
    requests: python module from pypi https://pypi.python.org/pypi/requests
        At least version 2.4.2 is required.

Examples:
```
# Get your Bitcoin balance using automatic credential detection
coin_balance {
    cache_timeout = 45
    format = "My BTC: {bitcoin}"
    host = "localhost"
    protocol = "http"
}

# Get your Bitcoin, Dogecoin and Litecoin balances using specific credentials
# for Bitcoin and automatic detection for Dogecoin and Litecoin
coin_balance {
    # ...
    format = "{bitcoin} BTC {dogecoin} XDG {litecoin} LTC"
    bitcoin_username = "lcdata"
    bitcoin_password = "omikron-theta"
    # ...
}

# Get your Dogecoin and Litecoin balances using 'global' credentials
coin_balance {
    # ...
    format = "XDG: {dogecoin} LTC: {litecoin}"
    username = "crusher_b"
    password = "WezRulez"
    # ...
}

# Get you Dogecoin, Litecoin, and Bitcoin balances by using 'global'
# credentials for Bitcoin and Dogecoin but specific credentials for
# Litecoin.
coin_balance {
    # ...
    format = "XDG: {dogecoin} LTC: {litecoin} BTC: {bitcoin}"
    username = "zcochrane"
    password = "sunny_islands"
    litecoin_username = 'locutus'
    litecoin_password = 'NCC-1791-D'
    # ...
}
```

@author Felix Morgner <felix.morgner@gmail.com>
@license 3-clause-BSD

SAMPLE OUTPUT
{'full_text': 'LTC: 90.6428'}
"""

from errno import ENOENT
from os.path import expanduser
import requests
from string import Formatter


COIN_PORTS = {"bitcoin": 8332, "dogecoin": 22555, "litecoin": 9332}

REQUEST = {"method": "getbalance"}


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 30
    coin_password = None
    coin_username = None
    credentials = None
    format = "LTC: {litecoin}"
    host = "localhost"
    password = None
    protocol = "http"
    username = None

    def post_config_hook(self):
        self._active_coins = []
        self._config = None
        self._credential_cache = {}

    def coin_balance(self, outputs, config):
        self._config = config

        self._active_coins = [e[1] for e in Formatter().parse(self.format)]
        balances = {}
        for coin in self._active_coins:
            balances[coin] = self._get_balance(coin)

        return {
            "full_text": self.py3.safe_format(self.format, balances),
            "cached_until": self.py3.time_in(self.cache_timeout),
        }

    def _get_daemon_config_value(self, coin, key):
        try:
            with open(expanduser("~/.{0}/{0}.conf".format(coin)), "r") as cfg:
                for line in cfg.readlines():
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    fields = line.split("=", 1)
                    if len(fields) == 2 and fields[0].strip() == key:
                        return fields[1].strip()
        except IOError as err:
            if err.errno == ENOENT:
                return
            raise

    def _get_credentials(self, coin):
        if coin not in self._credential_cache:
            username = getattr(self, "{}_username".format(coin), None)
            if username is None:
                username = getattr(self, "username", None)
            if username is None:
                username = self._get_daemon_config_value(coin, "rpcuser")

            password = getattr(self, "{}_password".format(coin), None)
            if password is None:
                password = getattr(self, "password", None)
            if password is None:
                password = self._get_daemon_config_value(coin, "rpcpassword")

            self._credential_cache[coin] = {"username": username, "password": password}

        return self._credential_cache[coin]

    def _get_balance(self, coin):
        if coin not in COIN_PORTS:
            return "Unsupported coin"

        credentials = self._get_credentials(coin)

        try:
            auth_data = requests.auth.HTTPBasicAuth(**credentials)
            url = "{protocol}://{host}:{port}".format(
                protocol=self.protocol, host=self.host, port=COIN_PORTS[coin]
            )

            res = requests.post(url=url, auth=auth_data, json=REQUEST)

            if res.status_code == requests.codes.ok:
                return res.json().get("result", None)
            elif res.status_code == requests.codes.unauthorized:
                return "Authentication failed"
            else:
                return "Request Error"
        except:  # noqa e722
            return "Connection to '" + url + "' failed"


if __name__ == "__main__":
    from py3status.module_test import module_test

    config = {
        "litecoin_username": "geordi",
        "litecoin_password": "WarpByBrahms",
        "username": "leah",
        "password": "IDontLikeLaForge",
        "format": "LTC {litecoin} / BTC {bitcoin} / XDG {dogecoin} / {uknwn}",
    }
    module_test(Py3status, config)
