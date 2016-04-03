# -*- coding: utf-8 -*-
"""
Toggle monitor output from the status bar using xrandr.

Configuration parameters:
    - cache_timeout : how often we refresh usage in seconds (default: 10s)
    - distext : custom text or symbol for disconnected status
    - format : see placeholders below
    - number : number of the monitor we want to query
    - offtext : custom text or symbol for off status
    - ontext : custom text or symbol for on status
    - position : where the monitor will be toggled (ex: left-of HDMI-1)
    - source : name of the source we want to query (ex: HDMI-2)

Format of status string placeholders:
    {monitor} : monitor source name
    {status} : on/off status

Example config:

```
xrandr_toggle {
    # we could use the monitor number from xrandr output
    # name = "1"
    # or the monitor id directly
    source = "HDMI-2"
    position = "left-of DVI-I-1"
    format = "[{monitor}:TV32\"]"
}
```

@author mrt-prodz
"""
from subprocess import call, check_output
from re import search
from time import time


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    distext = 'disconnected'
    format = '{source}:{status}'
    number = '1'
    offtext = 'off'
    ontext = 'on'
    position = ''
    source = ''

    def __init__(self):
        self.mon = None
        self.status = self._xrandr()

    # return error occurs
    def _error_response(self, color, text):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': 'xrandr_toggle: ' + text,
            'color': color
        }
        return response

    # query xrandr for monitors status
    def _xrandr(self):
            return check_output(['xrandr']).split('\n')

    # return connected monitor using xrandr and number for index
    def get_status(self, i3s_output_list, i3s_config):
        try:
            # monitor number (index) must be bigger than 0
            number = int(self.number) - 1
            if number < 0:
                return self._error_response(i3s_config['color_bad'],
                                            'invalid number')
            monitors = []
            # width x height + left + top
            regex = r'\d{1,}x\d{1,}\+\d{1,}\+\d{1,}'
            # for each line find (dis)connected monitors
            for line in self.status:
                if 'connected' in line:
                    details = line.split(' ')
                    if len(details) > 2:
                        source = {}
                        source['id'] = details[0]
                        if details[1] == 'disconnected':
                            source['connected'] = 0
                            source['state'] = 'off'
                            source['status'] = self.distext
                        else:
                            source['connected'] = 1
                            if search(regex, details[2]):
                                source['state'] = 'auto'
                                source['status'] = self.ontext
                            else:
                                source['state'] = 'off'
                                source['status'] = self.offtext
                        monitors.append(source)

            # index bigger than array of monitors found
            if number >= len(monitors):
                return self._error_response(i3s_config['color_bad'],
                                            'number is too high')
            # if source is set, use that instead of number
            if len(self.source) > 0:
                self.mon = next((x for x in monitors
                                if x['id'] == self.source),
                                None)
                if self.mon is None:
                    return self._error_response(i3s_config['color_bad'],
                                                'monitor not found')
            else:
                self.mon = monitors[number]

            if self.mon['connected'] == 0:
                color = i3s_config['color_bad']
            elif self.mon['state'] == 'auto':
                color = i3s_config['color_good']
            else:
                color = i3s_config['color_degraded']

            response = {
                'cached_until': time() + self.cache_timeout,
                'color': color,
                'full_text': self.format.format(monitor=self.mon['id'],
                                                status=self.mon['status'])
            }
            return response
        except:
            return self._error_response(i3s_config['color_bad'], 'error')

    # toggle source on/off
    def on_click(self, i3s_output_list, i3s_config, event):
        if (self.mon is not None) and (self.mon['connected'] == 1):
            command = ['xrandr', '--output', self.mon['id']]
            if self.mon['state'] == 'auto':
                state = 'off'
            else:
                state = 'auto'
                if len(self.position) > 0:
                    pos = self.position.split(' ')
                    if len(pos) == 2:
                        command.append('--' + pos[0])
                        command.append(pos[1])
            command.append('--' + state)
            call(command)
            # update status
            self.status = self._xrandr()


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_degraded': '#00FFFF',
        'color_bad': '#FF0000'
    }
    print(x.get_status([], config))
