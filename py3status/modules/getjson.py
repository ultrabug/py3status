# -*- coding: utf-8 -*-
"""
Query a url and display the json response

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 30)
    delimiter: the delimiter between parent and child objects
        (default '-')
    format: placeholders will be replaced by the returned json key names
        (default None)
    timeout: how long before deciding we're offline
        (default 5)
    url: specify a url to fetch json from
        (default None)

Format placeholders:
    Placeholders will be replaced by the json keys

    Placeholders for objects with sub-objects are flattened using 'delimiter' in between
        (eg. {'parent': {'child': 'value'}} will use placeholder {parent-child}

    Placeholders for list elements have 'delimiter' followed by the index
        (eg. {'parent': ['this', 'that']) will use placeholders {parent-0} for 'this' and
        {parent-1} for 'that'

@author vicyap
"""

import collections
import json
try:
    # python3
    from urllib.request import urlopen
except:
    from urllib2 import urlopen


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 30
    delimiter = '-'
    format = None
    timeout = 5
    url = None

    def _flatten(self, d, parent_key=None):
        """Flatten a dictionary.

        Values that are dictionaries are flattened using self.delimiter in between
            (eg. parent-child)
        Values that are lists are flattened using self.delimiter followed by the index
            (eg. parent-0)
        """
        items = []
        for k, v in d.items():
            if parent_key:
                k = u'{}{}{}'.format(parent_key, self.delimiter, k)
            if isinstance(v, list):
                v = dict(enumerate(v))
            if isinstance(v, collections.Mapping):
                items.append((k, v))
                items.extend(self._flatten(v, k).items())
            else:
                items.append((k, v))
        return dict(items)

    def _query_url(self):
        """
        """
        try:
            resp = urlopen(self.url, timeout=self.timeout)
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
            'cached_until': self.py3.time_in(self.cache_timeout),
        }

        resp, status = self._query_url()

        if status:
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
