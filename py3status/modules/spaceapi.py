# -*- coding: utf-8 -*-
"""
This module shows if your favorite hackerspace is open or not

Last modified: 2015-02-01
Author: @timmszigat
License: WTFPL http://www.wtfpl.net/txt/copying/
"""

from time import time
import datetime
import json
import urllib.request
import codecs

class Py3status:
    """
    Configuration Parameters:
      - cache_timeout: Set timeout between calls in seconds
      - url: URL to SpaceAPI json file of your space
      - open_text: text if space is open, strftime parmeters will be translated
      - open_color: color if space is open
      - closed_text: text if space is closed, strftime parameters will be translated
      - closed_color: color if space is closed
    """

    # available configuration parameters
    cache_timeout = 60
    url = 'http://status.chaospott.de/status.json'
    open_text = 'open since %H:%M'
    open_color = None
    closed_text = 'closed since %H:%M'
    closed_color = None

    def check(self, i3s_output_list, i3s_config):

        response = {
            'name': 'spaceapi',
            'cached_until': time() + self.cache_timeout
            }

        try:
            # if color isn't set, set basic color schema
            if not self.open_color:
                self.open_color = i3s_config['color_good']

            if not self.closed_color:
                self.closed_color = ''

            
            # grab json file 
            json_file=urllib.request.urlopen(self.url)
            reader = codecs.getreader("utf-8")
            data = json.load(reader(json_file))
            json_file.close()
            
            
            if(data['state']['open'] == True):
                response['full_text'] = self.open_text
                response['short_text'] = '%H:%M'
                if self.open_color:
                    response['color'] = self.open_color
            else:
                response['full_text'] = self.closed_text
                response['short_text'] = ''
                if self.closed_color:
                    response['color'] = self.closed_color

            # apply strftime to full and short text
            dt = datetime.datetime.fromtimestamp(data['state']['lastchange'])
            response['full_text'] = dt.strftime(response['full_text'])
            response['short_text'] = dt.strftime(response['short_text'])

        except:
            response['full_text'] = '';


        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.check([], {'color_good': 'green'}))
        sleep(1)
