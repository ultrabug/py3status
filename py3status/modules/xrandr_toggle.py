# -*- coding: utf-8 -*-
"""
Toggles a monitor on or off from the status bar using xrandr.

Configuration parameters:
    cache_timeout: how often we refresh usage in seconds (default: 10s)
    format: see placeholders below
    format_disconnected: custom text or symbol for disconnected status
    format_off: custom text or symbol for off status
    format_on: custom text or symbol for on status
    number: number of the monitor we want to query
    position: where the monitor will be toggled (ex: left-of HDMI-1)
    source: name of the source we want to query (ex: HDMI-2)

Format of status string placeholders:
    {screen} screen source name
    {status} on/off status

Example config:

```
xrandr_toggle {
    # we could use the monitor number from xrandr output
    # name = "1"
    # or the monitor id directly
    source = "HDMI-2"
    position = "left-of DVI-I-1"
    format = "[{screen}:TV32\"]"
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
    format = '{source}:{status}'
    format_disconnected = 'disconnected'
    format_on = 'on'
    format_off = 'off'
    number = '1'
    position = ''
    source = ''

    def __init__(self):
        self.monitor = None
        self.monitors = self._xrandr()

    # return error occurs
    def _error(self, text, color=None):
        if color is None:
            color = '#FF0000'
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': 'xrandr_toggle: ' + text,
            'color': color
        }
        return response

    # query xrandr for monitors status
    def _xrandr(self):
        try:
            status = check_output(['xrandr']).split('\n')
            monitors = []
            # width x height + left + top
            regex = r'\d{1,}x\d{1,}\+\d{1,}\+\d{1,}'
            # for each line find (dis)connected monitors
            for line in status:
                if 'connected' in line:
                    details = line.split(' ')
                    if len(details) > 2:
                        source = {}
                        source['id'] = details[0]
                        if details[1] == 'disconnected':
                            source['connected'] = 0
                            source['state'] = 'off'
                        else:
                            source['connected'] = 1
                            if search(regex, details[2]):
                                source['state'] = 'auto'
                            else:
                                source['state'] = 'off'
                        monitors.append(source)
            return monitors
        except:
            return None

    # return connected monitor using xrandr and number for index
    def get_status(self, i3s_output_list, i3s_config):
        try:
            color_bad = i3s_config['color_bad']
            color_degraded = i3s_config['color_degraded']
            color_good = i3s_config['color_good']
            # make sure we have stored a monitors list
            if self.monitors is None:
                return self._error('xrandr output parsing error', color_bad)
            # monitor number (index) must be bigger than 0
            number = int(self.number) - 1
            if number < 0:
                return self._error('invalid number', color_bad)
            # index bigger than array of monitors found
            if number >= len(self.monitors):
                return self._error('number is too high', color_bad)
            # if source is set, use that instead of number
            if len(self.source) > 0:
                self.monitor = None
                for x in self.monitors:
                    if x['id'] == self.source:
                        self.monitor = x
                        break
                if self.monitor is None:
                    return self._error('monitor not found', color_bad)
            else:
                self.monitor = self.monitors[number]
            # set color and custom status
            if self.monitor['connected'] == 0:
                color = color_bad
                self.monitor['status'] = self.format_disconnected
            elif self.monitor['state'] == 'auto':
                color = color_good
                self.monitor['status'] = self.format_on
            else:
                color = color_degraded
                self.monitor['status'] = self.format_off

            response = {
                'cached_until': time() + self.cache_timeout,
                'color': color,
                'full_text': self.format.format(screen=self.monitor['id'],
                                                status=self.monitor['status'])
            }
            return response
        except Exception as e:
            return self._error(e.message, color_bad)

    # toggle source on/off
    def on_click(self, i3s_output_list, i3s_config, event):
        if (self.monitor is not None) and (self.monitor['connected'] == 1):
            command = ['xrandr', '--output', self.monitor['id']]
            if self.monitor['state'] == 'auto':
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
            self.monitors = self._xrandr()


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
