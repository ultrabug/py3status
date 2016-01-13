# -*- coding: utf-8 -*-
"""
Display Icinga2 service status information

Configuration Parameters:
    - cache_timeout: how often the data should be updated
    - base_url: the base url to the icinga-web2 services list
    - disable_acknowledge: enable or disable counting of acknowledged service problems
    - user: username to authenticate against the icinga-web2 interface
    - password: password to authenticate against the icinga-web2 interface
    - format: define a format string like "CRITICAL: %d"
    - color: define a color for the output
    - status: set the status you want to optain (0=OK,1=WARNING,2=CRITICAL,3=UNKNOWN)

@author Ben Oswald <ben.oswald@root-space.de>
@license MIT License <https://opensource.org/licenses/MIT>
@source https://github.com/nazco/i3status-modules
"""
from time import time
import requests

class Py3status:
    """
    """
    STATUS_NAMES = {
            0: 'OK',
            1: 'WARNING',
            2: 'CRITICAL',
            3: 'UNKNOWN'
            }
    # available configuration parameters
    cache_timeout = 60
    base_url = ''
    disable_acknowledge = False
    url_parameters = "?service_state={service_state}&format=json"
    user = ''
    password = ''
    ca = True
    format = '{status_name}: {count}'
    color = '#ffffff'
    status = 0

    def get_status(self, i3s_output_list, i3s_config):
        response = {
            'color': self.color,
            'cached_until': time() + self.cache_timeout,
            'full_text': self.format.format(
                status_name=self.STATUS_NAMES.get(self.status),
                count=self._query_service_count(self.status)
                )
        }
        return response

    def _query_service_count(self, state):
        if self.disable_acknowledge:
            self.url_parameters = self.url_parameters + "&service_handled=0"
        result = requests.get(
            self.base_url + self.url_parameters.format(service_state=state),
            auth=(self.user, self.password), verify=self.ca)
        return len(result.json())

if __name__ == "__main__":
    pass
