# -*- coding: utf-8 -*-
"""
py3status module to display the mullvad VPN status.

"""

import requests


class Py3status:
    def check(self):
        res = requests.get('https://am.i.mullvad.net/json')
        if res.status_code != 200:
            return {
                    'color': '#FF0000',
                    'full_text': 'Mullvad: Error'
                    }

        status = res.json()
        if status['mullvad_exit_ip'] is False:
            return {
                    'color': '#FF0000',
                    'full_text': 'Mullvad: Down'
                    }
        else:
            return {
                    'color': '#00FF00',
                    'full_text': 'Mullvad: {}'.format(status['country'])
                    }

