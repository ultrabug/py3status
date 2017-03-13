# -*- coding: utf-8 -*-
"""
Display status of a given hackerspace.

Configuration parameters:
    button_url: Button that when clicked opens the URL sent in the space's API.
        Setting to None disables. (default 3)
    cache_timeout: Set timeout between calls in seconds (default 60)
    closed_text: text if space is closed, strftime parameters
        will be translated (default 'closed')
    open_text: text if space is open, strftime parmeters will be translated
        (default 'open')
    time_text: format used for time display (default ' since %H:%M')
    url: URL to SpaceAPI json file of your space
        (default 'http://status.chaospott.de/status.json')

Color options:
    color_closed: Space is open, defaults to color_bad
    color_open: Space is closed, defaults to color_good

@author timmszigat
@license WTFPL <http://www.wtfpl.net/txt/copying/>

SAMPLE OUTPUT
{'color': '#FF0000', 'full_text': 'closed since 16:38'}
"""

import datetime


class Py3status:
    """
    """
    # available configuration parameters
    button_url = 3
    cache_timeout = 60
    closed_text = 'closed'
    open_text = 'open'
    time_text = ' since %H:%M'
    url = 'http://status.chaospott.de/status.json'

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'open_color',
                    'new': 'color_open',
                    'msg': 'obsolete parameter use `color_open`',
                },
                {
                    'param': 'closed_color',
                    'new': 'color_closed',
                    'msg': 'obsolete parameter use `color_closed`',
                },
            ],
        }

    def check(self):

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
        }

        try:
            data = self.py3.request(self.url).json()
            self._url = data.get('url')

            if(data['state']['open'] is True):
                response['color'] = self.py3.COLOR_OPEN or self.py3.COLOR_GOOD
                if 'lastchange' in data['state'].keys():
                    response['full_text'] = self.open_text + self.time_text
                    response['short_text'] = '%H:%M'
                else:
                    response['full_text'] = self.open_text
                    response['short_text'] = self.open_text

            else:
                response['color'] = self.py3.COLOR_CLOSED or self.py3.COLOR_BAD
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

    def on_click(self, event):
        button = event['button']
        if self._url and self.button_url == button:
            cmd = 'xdg-open {}'.format(self._url)
            self.py3.command_run(cmd)
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
