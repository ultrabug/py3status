# -*- coding: utf-8 -*-
"""
A simple stopwatch.

This is a very basic stopwatch. You can start, pause and reset the
stopwatch.

Button 1 starts/pauses the stopwatch.
Button 2 resets stopwatch.

Configuration parameters:
    format: display format for this module (default 'Stopwatch {stopwatch}')

Format placeholders:
    {stopwatch} display hours:minutes:seconds

@author Jonas Heinrich

SAMPLE OUTPUT
{'full_text': 'Stopwatch 0:01:00'}

running
[
    {'full_text': 'Stopwatch '},
    {'color': '#00FF00', 'full_text': '0'},
    {'full_text': ':'},
    {'color': '#00FF00', 'full_text': '00'},
    {'full_text': ':'},
    {'color': '#00FF00', 'full_text': '54'},
]

paused
[
    {'full_text': 'Stopwatch '},
    {'color': '#FFFF00', 'full_text': '0'},
    {'full_text': ':'},
    {'color': '#FFFF00', 'full_text': '00'},
    {'full_text': ':'},
    {'color': '#FFFF00', 'full_text': '54'},
]
"""

from time import time


class Py3status:
    """
    """
    # available configuration parameters
    format = 'Stopwatch {stopwatch}'
    button_reset = 3
    button_toggle = 1

    def _reset_time(self):
        self.running = False
        self.paused = False
        self.time_state = None
        self.color = None

    def post_config_hook(self):
        self.time_start = None
        self._reset_time()

    def stopwatch(self):

        if self.running:
            cached_until = self.py3.time_in(0, offset=1)
            t = int(time() - self.time_start)
        else:
            cached_until = self.py3.CACHE_FOREVER
            if self.time_state:
                t = self.time_state
            else:
                t = 0

        hours, t = divmod(t, 3600)
        minutes, t = divmod(t, 60)
        seconds = t

        composites = [
            {
                'full_text': str(hours),
                'color': self.color,
            },
            {
                'color': self.color,
                'full_text': ':',
            },
            {
                'full_text': '%02d' % (minutes),
                'color': self.color,
            },
            {
                'color': self.color,
                'full_text': ':',
            },
            {
                'full_text': '%02d' % (seconds),
                'color': self.color,
            },
        ]

        stopwatch = self.py3.composite_create(composites)

        return {
            'cached_until': cached_until,
            'full_text': self.py3.safe_format(
                self.format, {'stopwatch': stopwatch})
        }

    def on_click(self, event):
        button = event['button']

        if button == self.button_toggle:
            if self.running:
                # pause stopwatch
                self.running = False
                self.paused = True
                self.time_state = int(time() - self.time_start)
                self.color = self.py3.COLOR_BAD
            else:
                self.color = self.py3.COLOR_GOOD
                self.running = True
                # start/restart stopwatch
                if self.paused:
                    self.time_start = int(time() - self.time_state)
                else:
                    self.time_start = time()

        if button == self.button_reset:
            # reset and pause stopwatch
            self._reset_time()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
