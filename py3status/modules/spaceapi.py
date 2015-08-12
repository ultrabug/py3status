# -*- coding: utf-8 -*-
"""
Display if your favorite hackerspace is open or not.

Configuration Parameters:
    - cache_timeout: Set timeout between calls in seconds
    - closed_color: color if space is closed
    - closed_text: text if space is closed, strftime parameters will be translated
    - open_color: color if space is open
    - open_text: text if space is open, strftime parmeters will be translated
    - url: URL to SpaceAPI json file of your space

@author timmszigat
@license WTFPL <http://www.wtfpl.net/txt/copying/>
"""

import codecs
import datetime
import json
from time import time
import urllib.request


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 60
    closed_color = None
    closed_text = 'closed'
    open_color = None
    open_text = 'open'
    time_text = ' since %H:%M'
    url = 'http://status.chaospott.de/status.json'

    def check(self, i3s_output_list, i3s_config):

        response = {
            'cached_until': time() + self.cache_timeout
            }

        try:
            # if color isn't set, set basic color schema
            if not self.open_color:
                self.open_color = i3s_config['color_good']

            if not self.closed_color:
                self.closed_color = ''

            # grab json file
            json_file = urllib.request.urlopen(self.url)
            reader = codecs.getreader("utf-8")
            data = json.load(reader(json_file))
            json_file.close()

            if(data['state']['open'] is True):
                if self.open_color:
                    response['color'] = self.open_color
                if 'lastchange' in data['state'].keys():
                    response['full_text'] = self.open_text + self.time_text
                    response['short_text'] = '%H:%M'
                else:
                    response['full_text'] = self.open_text
                    response['short_text'] = self.open_text

            else:
                if self.closed_color:
                    response['color'] = self.closed_color
                if 'lastchange' in data['state'].keys():
                    response['full_text'] = self.closed_text + self.time_text
                    response['short_text'] = ''
                else:
                    response['full_text'] = self.closed_text
                    response['short_text'] = self.closed_text

            if 'lastchange' in data['state'].keys():
                # apply strftime to full and short text
                dt = datetime.datetime.fromtimestamp(data['state']['lastchange'])
                response['full_text'] = dt.strftime(response['full_text'])
                response['short_text'] = dt.strftime(response['short_text'])

        except:
            response['full_text'] = ''

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.check([], config))
        sleep(1)
