# -*- coding: utf-8 -*-

"""
Display balances of diverse crypto-currencies

This module grabs your current balance of different crypto-currents from a
wallet server. The server must conform to the bitcoin RPC specification.
Currently Bitcoin, Dogecoin, and Litecoin are supported.

Configuration parameters:
    cache_timeout: The time between refreshs (default 30)
    color: The color for the output (default color_good)
    format: The format string for the output (default 'LTC: {litecoin}')
    host: The server hostname (default 'localhost')
    protocol: The protocol to use to connect to the server (default 'http')

Format status string parameters:
    {bitcoin} Your bitcoin balance
    {dogecoin} Your dogecoin balance
    {litecoin} Your litecoin balance

Requires:
    requests: python module from pypi https://pypi.python.org/pypi/requests

Example:

```
# Get your bitcoin balance
coin_balance {
    cache_timeout = 45
    color = "#ffcd18"
    format = "My BTC: {bitcoin}"
    host = "localhost"
    protocol = "http"
}
```

@author Felix Morgner <felix.morgner@gmail.com>
@license 3-clause-BSD
"""

import json
from os.path import expanduser
from py3status.module_test import module_test
import requests
from string import Formatter


COIN_PORTS = {
    'bitcoin': 8332,
    'dogecoin': 22555,
    'litecoin': 9332,
}

HEADERS = {
    'content-type': 'application/json'
}

REQUEST = {
    'method': 'getbalance',
}

CREDENTIAL_FIELDS = {
    'rpcuser': 'username',
    'rpcpassword': 'password',
}


class Py3status:
    cache_timeout = 30
    color = None
    format = 'LTC: {litecoin}'
    host = 'localhost'
    protocol = 'http'

    _config = None

    def coin_balance(self, outputs, config):
        self._config = config
        if self.color is None:
            self.color = config['color_good']

        balances = {}
        for coin in [e[1] for e in Formatter().parse(self.format)]:
            balances[coin] = self._get_balance(coin)

        return {
            'full_text': self.py3.safe_format(self.format, balances),
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': self.color,
        }

    def _get_credentials(self, coin):
        try:
            with open(expanduser('~/.{0}/{0}.conf').format(coin)) as cfg:
                creds = {}
                for line in cfg.readlines():
                    fields = line.split('=')
                    if len(fields) == 2 and fields[0] in CREDENTIAL_FIELDS:
                        creds[CREDENTIAL_FIELDS[fields[0]]] = fields[1].strip()

                if all(key in creds for key in CREDENTIAL_FIELDS.values()):
                    return creds
        except FileNotFoundError:
            pass

            return None

    def _get_balance(self, coin):
        if coin not in COIN_PORTS:
            return 'Unsupported coin'

        try:
            credentials = self._get_credentials(coin)
            if credentials is None:
                self.color = self._config['color_bad']
                return 'Missing credentials for "{}"'.format(coin)

            auth_data = requests.auth.HTTPBasicAuth(**credentials)
            url = '{protocol}://{host}:{port}'.format(protocol=self.protocol,
                                                      host=self.host,
                                                      port=COIN_PORTS[coin])
            res = requests.post(url=url,
                                auth=auth_data,
                                data=json.dumps(REQUEST),
                                headers=HEADERS)

            if res.status_code == requests.codes.ok:
                return res.json().get('result', None)
            elif res.status_code == requests.codes.unauthorized:
                return 'Authentication failed'
            else:
                return 'Request Error'
        except:
            return 'Connection to \'' + url + '\' failed'

if __name__ == "__main__":
    module_test(Py3status)
