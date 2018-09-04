# -*- coding: utf-8 -*-
"""
Display calculated time spent and costs.

Configuration parameters:
    button_reset: mouse button to reset the timer (default 3)
    button_toggle: mouse button to toggle the timer (default 1)
    config_file: specify a file to save time between sessions
        (default '~/.config/py3status/rate_counter.save')
    format: display format for this module
        *(default 'Rate Counter [\?color=state [\?not_zero {days} days ]'
        '[\?not_zero {hours}:]{minutes}:{seconds}'
        '[\?color=darkgray&show \|]${total}]')*
    rate: specify the hourly pay rate to use (default 30)
    tax: specify the tax value to use, 1.02 is 2% (default 1.0)
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (1, 'good')])

Control placeholders:
    {state} running state, eg False, True

Format placeholders:
    {days}          number of days
    {hours}         number of hours
    {minutes}       number of minutes
    {rate}          inputted hourly rate
    {seconds}       number of seconds
    {subtotal}      subtotal cost (time * rate)
    {tax}           tax cost, based on the subtotal cost
    {total}         total cost (subtotal + tax)
    {total_hours}   total number of hours
    {total_minutes} total number of minutes

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author Amaury Brisou <py3status AT puzzledge.org>, lasers

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'0:00 / $0.00'}

running
{'color': '#FF0000', 'full_text': u'4:48 / $2.45'}
"""

import os
import time
SECONDS_IN_MIN = 60.0  # 60
SECONDS_IN_HOUR = 60.0 * SECONDS_IN_MIN  # 3600
SECONDS_IN_DAY = 24.0 * SECONDS_IN_HOUR  # 86400


class Py3status:
    """
    """
    # available configuration parameters
    button_reset = 3
    button_toggle = 1
    config_file = '~/.config/py3status/rate_counter.save'
    format = ('Rate Counter [\?color=state [\?not_zero {days} days ]'
              '[\?not_zero {hours}:]{minutes}:{seconds}'
              '[\?color=darkgray&show \|]${total}]')
    rate = 30
    tax = 1.00
    thresholds = [(0, 'bad'), (1, 'good')]

    class Meta:
        deprecated = {
            'remove': [
                {
                    'param': 'format_money',
                    'msg': 'obsolete parameter',
                },
            ],
            'rename': [
                {
                    'param': 'hour_price',
                    'new': 'rate',
                    'msg': 'obsolete parameter. use `rate`'
                },
            ],
            'rename_placeholder': [
                {
                    'placeholder': 'mins',
                    'new': 'minutes',
                    'format_strings': ['format'],
                },
                {
                    'placeholder': 'secs',
                    'new': 'seconds',
                    'format_strings': ['format'],
                },
                {
                    'placeholder': 'total_mins',
                    'new': 'total_minutes',
                    'format_strings': ['format'],
                },
            ],
        }
        update_config = {
            'update_placeholder_format': [
                {
                    'placeholder_formats': {
                        'total': ':.2f',
                        'total_minutes': ':.2f',
                        'total_seconds': ':.2f',
                    },
                    'format_strings': ['format']
                },
            ],
        }

    def post_config_hook(self):
        periods = [('*hours', 3600), ('*minutes', 60), ('*seconds', 0)]
        for name, cache in periods:
            if self.py3.format_contains(self.format, name):
                self.cache_timeout = cache

        self.thresholds_init = self.py3.get_color_names_list(self.format)
        self.config_file = os.path.expanduser(self.config_file)
        self.saved_time = 0
        self.start_time = self._current_time
        self.rate = float(self.rate)
        self.tax = float(self.tax)
        self._is_running = False

        try:
            with open(self.config_file) as f:
                self.saved_time = float(f.read())
        except: # noqa e722 // (IOError, FileNotFoundError):  # py2/py3
            pass

    @property
    def _current_time(self):
        return time.time()

    def _seconds_to_time(self, time_in_seconds):
        """
        Blindly using the days in `time.gmtime()` will fail if it is more than
        one month (days > 31). We're using days as the largest unit of time.
        """
        days = int(time_in_seconds / SECONDS_IN_DAY)
        remaining_seconds = time_in_seconds % SECONDS_IN_DAY
        hours = int(remaining_seconds / SECONDS_IN_HOUR)
        remaining_seconds = remaining_seconds % SECONDS_IN_HOUR
        minutes = '{:02d}'.format(int(remaining_seconds / SECONDS_IN_MIN))
        seconds = '{:02d}'.format(int(remaining_seconds % SECONDS_IN_MIN))
        return days, hours, minutes, seconds

    def _reset_timer(self):
        if not self._is_running:
            self.saved_time = 0
            try:
                with open(self.config_file, 'w') as f:
                    f.write('0')
            except:  # noqa e722 (untested)
                pass

    def _start_timer(self):
        if not self._is_running:
            self.start_time = self._current_time - self.saved_time
            self._is_running = True

    def _stop_timer(self):
        if self._is_running:
            self.saved_time = self._current_time - self.start_time
            self._is_running = False

    def _toggle_timer(self):
        if self._is_running:
            self._stop_timer()
        else:
            self._start_timer()

    def kill(self):
        self._stop_timer()
        try:
            with open(self.config_file, 'w') as f:
                f.write(str(self.saved_time))
        except:  # noqa e722 (untested)
            pass

    def rate_counter(self):
        if self._is_running:
            cached_until = self.cache_timeout
            running_time = self._current_time - self.start_time
        else:
            cached_until = self.py3.CACHE_FOREVER
            running_time = self.start_time = self.saved_time

        days, hours, minutes, seconds = self._seconds_to_time(running_time)
        total_hours = running_time / SECONDS_IN_HOUR
        total_minutes = running_time / SECONDS_IN_MIN

        subtotal = self.rate * total_hours
        total = subtotal * self.tax
        tax = total - subtotal

        rate_data = {
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'rate': self.rate,
            'seconds': seconds,
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
            'total_hours': total_hours,
            'total_minutes': total_minutes,
            'state': self._is_running,
        }

        for x in self.thresholds_init:
            if x in rate_data:
                self.py3.threshold_get_color(rate_data[x], x)

        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(self.format, rate_data)
        }

    def on_click(self, event):
        button = event['button']
        if button == self.button_toggle:
            self._toggle_timer()
        elif button == self.button_reset:
            self._reset_timer()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
