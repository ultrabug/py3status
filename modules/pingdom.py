# -*- coding: utf-8 -*-

import requests
from time import time


class Py3status:
    """
    Dynamically display the latest response time of the configured checks using
    the Pingdom API.
    We also verify the status of the checks and colorize if needed.
    Pingdom API doc : https://www.pingdom.com/services/api-documentation-rest/

    #NOTE: This module needs the 'requests' python module from pypi
        https://pypi.python.org/pypi/requests
    """
    def pingdom_checks(self, json, i3status_config):
        response = {'full_text': '', 'name': 'pingdom_checks'}

        #NOTE: configure me !
        APP_KEY = ''             # create an APP KEY on pingdom first
        CACHE_TIMEOUT = 600      # recheck every 10 mins
        CHECKS = []              # checks' names you want added to your bar
        LATENCY_THRESHOLD = 500  # when to colorize the output
        LOGIN = ''               # pingdom login
        PASSWORD = ''            # pingdom password
        TIMEOUT = 15
        POSITION = 0

        r = requests.get(
            'https://api.pingdom.com/api/2.0/checks',
            auth=(LOGIN, PASSWORD),
            headers={'App-Key': APP_KEY},
            timeout=TIMEOUT,
        )
        result = r.json()
        if 'checks' in result:
            for check in [
                ck for ck in result['checks'] if ck['name'] in CHECKS
            ]:
                if check['status'] == 'up':
                    response['full_text'] += '{}: {}ms, '.format(
                        check['name'],
                        check['lastresponsetime']
                    )
                    if check['lastresponsetime'] > LATENCY_THRESHOLD:
                        response.update(
                            {'color': i3status_config['color_degraded']}
                        )
                else:
                    response['full_text'] += '{}: DOWN'.format(
                        check['name'],
                        check['lastresponsetime']
                    )
                    response.update({'color': i3status_config['color_bad']})
            response['full_text'] = response['full_text'].strip(', ')
            response['cached_until'] = time() + CACHE_TIMEOUT

        return (POSITION, response)
