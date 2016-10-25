# -*- coding: utf-8 -*-
"""
Display the latest response time of the configured Pingdom checks.

We also verify the status of the checks and colorize if needed.
Pingdom API doc : https://www.pingdom.com/features/api/documentation/

Configuration parameters:
    app_key: create an APP KEY on pingdom first (default '')
    cache_timeout: how often to refresh the check from pingdom (default 600)
    checks: comma separated pindgom check names to display (default '')
    login: pingdom login (default '')
    max_latency: maximal latency before coloring the output (default 500)
    password: pingdom password (default '')
    request_timeout: pindgom API request timeout (default 15)

Color options:
    color_bad: Site is down
    color_degraded: Latency exceeded max_latency

Requires:
    requests: python module from pypi
        https://pypi.python.org/pypi/requests
"""

import requests


class Py3status:
    """
    """
    # available configuration parameters
    app_key = ''
    cache_timeout = 600
    checks = ''
    login = ''
    max_latency = 500
    password = ''
    request_timeout = 15

    def pingdom_checks(self):
        response = {'full_text': ''}

        # parse some configuration parameters
        if not isinstance(self.checks, list):
            self.checks = self.checks.split(',')

        r = requests.get(
            'https://api.pingdom.com/api/2.0/checks',
            auth=(self.login, self.password),
            headers={'App-Key': self.app_key},
            timeout=self.request_timeout,
        )
        result = r.json()
        if 'checks' in result:
            for check in [
                ck for ck in result['checks'] if ck['name'] in self.checks
            ]:
                if check['status'] == 'up':
                    response['full_text'] += '{}: {}ms, '.format(
                        check['name'],
                        check['lastresponsetime']
                    )
                    if check['lastresponsetime'] > self.max_latency:
                        response.update(
                            {'color': self.py3.COLOR_DEGRADED}
                        )
                else:
                    response['full_text'] += '{}: DOWN'.format(
                        check['name'],
                        check['lastresponsetime']
                    )
                    response.update({'color': self.py3.COLOR_BAD})
            response['full_text'] = response['full_text'].strip(', ')
            response['cached_until'] = self.py3.time_in(self.cache_timeout)

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
