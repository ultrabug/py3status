# -*- coding: utf-8 -*-
# FIXME closed_color, open_color params
"""
Display if your favorite hackerspace is open or not.

Configuration parameters:
    cache_timeout: Set timeout between calls in seconds (default 60)
    closed_color: color if space is closed (default None)
    closed_text: text if space is closed, strftime parameters
        will be translated (default 'closed')
    open_color: color if space is open (default None)
    open_text: text if space is open, strftime parmeters will be translated
        (default 'open')
    time_text: format used for time display (default ' since %H:%M')
    url: URL to SpaceAPI json file of your space
        (default 'http://status.chaospott.de/status.json')

@author timmszigat
@license WTFPL <http://www.wtfpl.net/txt/copying/>
"""

import codecs
import datetime
import json
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

    def check(self):

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            }

        try:
            # if color isn't set, set basic color schema
            if not self.open_color:
                self.open_color = self.py3.COLOR_GOOD

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
                dt = datetime.datetime.fromtimestamp(
                    data['state']['lastchange']
                )
                response['full_text'] = dt.strftime(response['full_text'])
                response['short_text'] = dt.strftime(response['short_text'])

        except:
            response['full_text'] = ''

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
