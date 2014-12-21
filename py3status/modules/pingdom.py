# -*- coding: utf-8 -*-
"""
Dynamically display the latest response time of the configured checks using
the Pingdom API.
We also verify the status of the checks and colorize if needed.
Pingdom API doc : https://www.pingdom.com/services/api-documentation-rest/

#NOTE: This module needs the 'requests' python module from pypi
    https://pypi.python.org/pypi/requests
"""

import requests
from time import time


class Py3status:
    """
    Configuration parameters:
        - app_key : create an APP KEY on pingdom first
        - cache_timeout : how often to refresh the check from pingdom
        - checks : comma separated pindgom check names to display
        - login : pingdom login
        - max_latency : maximal latency before coloring the output
        - password : pingdom password
        - request_timeout : pindgom API request timeout

    """
    # available configuration parameters
    app_key = ''
    cache_timeout = 600
    checks = ''
    login = ''
    max_latency = 500
    password = ''
    request_timeout = 15

    def pingdom_checks(self, i3s_output_list, i3s_config):
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
                            {'color': i3s_config['color_degraded']}
                        )
                else:
                    response['full_text'] += '{}: DOWN'.format(
                        check['name'],
                        check['lastresponsetime']
                    )
                    response.update({'color': i3s_config['color_bad']})
            response['full_text'] = response['full_text'].strip(', ')
            response['cached_until'] = time() + self.cache_timeout

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.pingdom_checks([], {}))
        sleep(1)
