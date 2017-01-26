# -*- coding: utf-8 -*-
"""
Query a url and display the json response

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 30)
    delimiter: the delimiter between parent and child objects
        (default '_')
    format: placeholders will be replaced by the returned json key names
        (default '')
    timeout: how long before deciding we're offline
        (default 5)
    url: specify a url to fetch json from
        (default '')

Format placeholders:
    Placeholders will be replaced by the json keys

    Placeholders for objects with sub-objects are flattened using 'delimiter' in between
        (eg. {'parent': {'child': 'value'}} will use placeholder {parent_child}

    Placeholders for list elements have 'delimiter' followed by the index
        (eg. {'parent': ['this', 'that']) will use placeholders {parent_0} for 'this' and
        {parent_1} for 'that'

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
    delimiter = '_'
    format = ''
    timeout = 5
    url = ''

    def _flatten(self, d, parent_key=None):
        """Flatten a dictionary.

        Values that are dictionaries are flattened using self.delimiter in between
            (eg. parent_child)
        Values that are lists are flattened using self.delimiter followed by the index
            (eg. parent_0)
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + self.delimiter + k if parent_key else k
            if isinstance(v, collections.Mapping):
                items.extend(self._flatten(v, new_key).items())
            elif isinstance(v, list):
                items.extend(
                    [(new_key + self.delimiter + str(i), str(x)) for i, x in enumerate(v)])
            else:
                items.append((new_key, v))
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
