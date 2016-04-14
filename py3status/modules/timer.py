# -*- coding: utf-8 -*-
"""
A simple countdown timer.

This is a very basic countdown timer.  You can change the timer length as well
as pausing, restarting and resetting it.  Currently this is more of a demo of a
composite and not really ready for production usage.

As well as a general clean it would be nice to have it play an alarm when the
time is up.  Ideally it should also run as a thread so that the alarm will go
off at the correct time.  It would be nice too if it could also survive a
py3status restart.

"""

from time import time


class Py3status:
    """
    """
    # available configuration parameters

    def __init__(self):
        self.time = 60
        self.running = False
        self.end_time = None
        self.time_left = None
        self.color = None

    def timer(self, i3s_output_list, i3s_config):

        def make_2_didget(value):
            value = str(value)
            if len(value) == 1:
                value = '0' + value
            return value

        if self.running:
            t = int(self.end_time - time())
            if t <= 0:
                t = 0
                self.running = False
                self.color = '#FF0000'
                self.time_left = None
        else:
            if self.time_left:
                t = self.time_left
            else:
                t = self.time

        # Hours
        hours, t = divmod(t, 3600)
        # Minutes
        mins, t = divmod(t, 60)
        # Seconds
        seconds = t

        if self.running:
            cached_until = time() + 1
        else:
            cached_until = self.py3.CACHE_FOREVER

        response = {
            'cached_until': cached_until,
            'composite': [
                {
                    'color': '#CCCCCC',
                    'full_text': 'Timer ',
                },
                {
                    'color': self.color,
                    'full_text': str(hours),
                    'index': 'hours',
                },
                {
                    'color': '#CCCCCC',
                    'full_text': ':',
                },
                {
                    'color': self.color,
                    'full_text': make_2_didget(mins),
                    'index': 'mins',
                },
                {
                    'color': '#CCCCCC',
                    'full_text': ':',
                },
                {
                    'color': self.color,
                    'full_text': make_2_didget(seconds),
                    'index': 'seconds',
                },
            ]
        }
        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        deltas = {
            'hours': 3600,
            'mins': 60,
            'seconds': 1
        }
        index = event['index']
        button = event['button']

        if button == 1:
            if self.running:
                self.running = False
                self.time_left = int(self.end_time - time())
                self.color = '#FFFF00'
            else:
                self.running = True
                if self.time_left:
                    self.end_time = time() + self.time_left
                else:
                    self.end_time = time() + self.time
                self.color = '#00FF00'

        if button == 2:
            self.running = False
            self.time_left = None
            self.color = None

        if not self.running:
            if self.time_left:
                t = self.time_left
            else:
                t = self.time
            if button == 4:
                t += deltas.get(index, 0)
            if button == 5:
                t -= deltas.get(index, 0)
                if t < 0:
                    t = 0
            if self.time_left:
                self.time_left = t
            else:
                self.time = t

        self.text = str(event['index'])

if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    print(x.timer([], config))
