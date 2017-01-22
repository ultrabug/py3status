# -*- coding: utf-8 -*-
"""
Query a url and display the json response

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 30)
    format: placeholders will be replaced by the returned json key names
        (default '')
    negative_cache_timeout: how often to check again when offline
        (default 2)
    params: specify the parameters to pass to the url as a dict
        (default {})
    sep: the separator between parent and child objects
        (default '_')
    timeout: how long before deciding we're offline
        (default 5)
    url: specify a url to fetch json from
        (default '')

Format placeholders:
    Placeholders will be replaced by the json keys
    Placeholders for objects with sub-objects are flattened using 'sep' in between
    (eg. {'parent': {'child': 'value'}} will use placeholder {parent_child}

@author vicyap
"""

import collections
import json
try:
    # python3
    from urllib.parse import urlencode
    from urllib.request import urlopen
except:
    from urllib import urlencode
    from urllib2 import urlopen


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 30
    format = ''
    negative_cache_timeout = 2
    params = {}
    sep = '_'
    timeout = 5
    url = ''

    def _flatten(self, d, parent_key=None):
        '''
        modified from http://stackoverflow.com/a/6027615
        '''
        items = []
        for k, v in d.iteritems():
            new_key = parent_key + self.sep + k if parent_key else k
            if isinstance(v, collections.Mapping):
                items.extend(self._flatten(v, new_key).iteritems())
            else:
                items.append((new_key, v))
        return dict(items)

    def _query_url(self):
        """
        """
        try:
            url = '{}?{}'.format(self.url, urlencode(self.params, True))
            resp = urlopen(url, timeout=self.timeout)
            status = resp.getcode() == 200
            resp = json.loads(resp.read())
        except Exception:
            resp = None
            status = False
        return resp, status

    def getjson(self):
        """
        """
        response = {
            'cached_until': self.py3.time_in(self.negative_cache_timeout),
        }

        resp, status = self._query_url()

        if status:
            response['cached_until'] = self.py3.time_in(self.cache_timeout)
            response['full_text'] = self.py3.safe_format(self.format, self._flatten(resp))
        else:
            response['full_text'] = ''
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
