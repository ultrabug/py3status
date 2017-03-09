# -*- coding: utf-8 -*-
"""
Display status of a given hackerspace.

Configuration parameters:
    button_url: mouse button to open URL sent in space's API (default 3)
    cache_timeout: refresh interval for this module (default 60)
    format: display format for this module (default '{spaceapi}')
    icon_closed: show when hackerspace is closed (default 'closed')
    icon_open: show when hackerspace is open (default 'open')
    icon_time: display format for time (default ' since %H:%M')
    url: specify JSON URL of a hackerspace to retrieve from
        (default 'http://status.chaospott.de/status.json')

__Note: Strftime parameters in icon_* parameters will be translated.__

Color options:
    color_bad: Space closed
    color_good: Space open

@author timmszigat
@license WTFPL <http://www.wtfpl.net/txt/copying/>
"""

import datetime
STRING_UNAVAILABLE = 'spaceapi: N/A'


class Py3status:
    """
    """
    # available configuration parameters
    button_url = 3
    cache_timeout = 60
    format = '{spaceapi}'
    icon_closed = 'closed'
    icon_open = 'open'
    icon_time = ' since %H:%M'
    url = 'http://status.chaospott.de/status.json'

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'open_color',
                    'new': 'color_good',
                    'msg': 'obsolete parameter use `color_good`',
                },
                {
                    'param': 'closed_color',
                    'new': 'color_bad',
                    'msg': 'obsolete parameter use `color_bad`',
                },
                {
                    'param': 'color_open',
                    'new': 'color_good',
                    'msg': 'obsolete parameter use `color_good`',
                },
                {
                    'param': 'color_closed',
                    'new': 'color_bad',
                    'msg': 'obsolete parameter use `color_bad`',
                },
                {
                    'param': 'closed_text',
                    'new': 'icon_closed',
                    'msg': 'obsolete parameter use `icon_closed`',
                },
                {
                    'param': 'open_text',
                    'new': 'icon_open',
                    'msg': 'obsolete parameter use `icon_open`',
                },
                {
                    'param': 'time_text',
                    'new': 'icon_time',
                    'msg': 'obsolete parameter use `icon_time`',
                },
            ],
        }

    def spaceapi(self):
        color = self.py3.COLOR_BAD
        full_text = self.icon_closed

        try:
            data = self.py3.request(self.url).json()
            self._url = data.get('url')

            if(data['state']['open']):
                color = self.py3.COLOR_GOOD
                full_text = self.icon_open

            if 'lastchange' in data['state'].keys():
                full_text += self.icon_time
                dt = datetime.datetime.fromtimestamp(data['state']['lastchange'])
                full_text = dt.strftime(full_text)

            full_text = self.py3.safe_format(self.format, {'spaceapi': full_text})
        except:
            full_text = STRING_UNAVAILABLE
        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text,
            'color': color
        }

    def on_click(self, event):
        button = event['button']
        if self._url and self.button_url == button:
            self.py3.command_run('xdg-open {}'.format(self._url))
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
