# -*- coding: utf-8 -*-
"""
Display Icinga2 service status information.

Configuration Parameters:
    base_url: the base url to the icinga-web2 services list
    cache_timeout: how often the data should be updated
    color: define a color for the output
    disable_acknowledge: enable or disable counting of acknowledged
        service problems
    format: define a format string like "CRITICAL: %d"
    password: password to authenticate against the icinga-web2 interface
    status: set the status you want to obtain
        (0=OK,1=WARNING,2=CRITICAL,3=UNKNOWN)
    user: username to authenticate against the icinga-web2 interface

@author Ben Oswald <ben.oswald@root-space.de>
@license BSD License <https://opensource.org/licenses/BSD-2-Clause>
@source https://github.com/nazco/i3status-modules
"""
from time import time
import requests

STATUS_NAMES = {0: 'OK', 1: 'WARNING', 2: 'CRITICAL', 3: 'UNKNOWN'}


class Py3status:
    """
    """
    # available configuration parameters
    base_url = ''
    ca = True
    cache_timeout = 60
    color = '#ffffff'
    disable_acknowledge = False
    format = '{status_name}: {count}'
    password = ''
    status = 0
    url_parameters = "?service_state={service_state}&format=json"
    user = ''

    def get_status(self, i3s_output_list, i3s_config):
        response = {
            'color': self.color,
            'cached_until': time() + self.cache_timeout,
            'full_text': self.format.format(
                status_name=STATUS_NAMES.get(self.status, "INVALID STATUS"),
                count=self._query_service_count(self.status))
        }
        return response

    def _query_service_count(self, state):
        url_parameters = self.url_parameters
        if self.disable_acknowledge:
            url_parameters = url_parameters + "&service_handled=0"
        result = requests.get(
            self.base_url + url_parameters.format(service_state=state),
            auth=(self.user, self.password),
            verify=self.ca)
        return len(result.json())


if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.get_status([], config)['full_text'])
        sleep(1)
