"""
Display JSON data fetched from a URL.

This module gets the given `url` configuration parameter and assumes the
response is a JSON object. The keys of the JSON object are used as the format
placeholders. The format placeholders are replaced by the value. Objects that
are nested can be accessed by using the `delimiter` configuration parameter
in between.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 30)
    delimiter: the delimiter between parent and child objects (default '-')
    format: display format for this module (default None)
    password: basic auth password information (default None)
    url: specify URL to fetch JSON from (default None)
    username: basic auth user information (default None)

Format placeholders:
    Placeholders will be replaced by the JSON keys.

    Placeholders for objects with sub-objects are flattened using 'delimiter'
    in between (eg. {'parent': {'child': 'value'}} will use placeholder
    {parent-child}).

    Placeholders for list elements have 'delimiter' followed by the index
    (eg. {'parent': ['this', 'that']) will use placeholders {parent-0}
    for 'this' and {parent-1} for 'that'.

Examples:
```
# straightforward key replacement
getjson {
    url = "https://ifconfig.co/json"
    format = "{latitude}, {longitude}"
}

# access child objects
getjson {
    url = 'https://api.icndb.com/jokes/random'
    format = '{value-joke}'
}

# access title from 0th element of articles list
getjson {
    url = 'https://newsapi.org/v1/articles?source=bbc-news&sortBy=top&apiKey={KEY}'
    format = '{articles-0-title}'
}

# access if top-level object is a list
getjson {
    url = 'https://jsonplaceholder.typicode.com/posts/1/comments'
    format = '{0-name}'
}
```

@author vicyap

SAMPLE OUTPUT
{'full_text': 'Github: Everything operating normally'}
"""

STRING_ERROR = "missing url"


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 30
    delimiter = "-"
    format = None
    password = None
    url = None
    username = None

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "timeout",
                    "new": "request_timeout",
                    "msg": "obsolete parameter use `request_timeout`",
                }
            ]
        }

    def post_config_hook(self):
        if not self.url:
            raise Exception(STRING_ERROR)

    def getjson(self):
        """ """
        try:
            if self.username is not None and self.password is not None:
                auth = (self.username, self.password)
            else:
                auth = None
            json_data = self.py3.request(self.url, auth=auth).json()
            json_data = self.py3.flatten_dict(json_data, self.delimiter, True)
        except self.py3.RequestException:
            json_data = None

        if json_data:
            full_text = self.py3.safe_format(self.format, json_data)
        else:
            full_text = ""

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
