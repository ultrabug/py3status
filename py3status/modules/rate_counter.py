# -*- coding: utf-8 -*-
"""
Display calculated time spent and costs.

Configuration parameters:
    button_reset: mouse button to reset the timer (default 3)
    button_toggle: mouse button to toggle the timer (default 1)
    config_file: specify a file to save time between sessions
        (default '~/.config/py3status/rate_counter.save')
    format: display format for this module
        *(default '\?color=running \u2295[\?not_zero {days} days ]'
        '[\?not_zero {hours}:]{minutes}:{seconds} / ${total}')*
    rate: specify the hourly pay rate to use (default 30)
    tax: specify the tax value to use, 1.02 is 2% (default 1.02)
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (1, 'good')])

Format placeholders:
    {days} The number of days in running timer
    {hours} The remaining number of hours in running timer
    {minutes} The remaining number of minutes in running timer
    {rate} The user inputted hourly rate
    {seconds} The remaining number of seconds in running timer
    {subtotal} The subtotal cost (time * rate)
    {tax} The tax cost, based on the subtotal cost
    {total} The total cost (subtotal + tax)
    {total_hours} The total number of hours in running timer
    {total_minutes} The total number of minutes in running timer

    For numeral placeholders, you can use `{placeholder:.0f}` to indicate a
    precision of a floating point to display the value in or `{placeholder:d}`
    to display the value in a decimal integer.

Color thresholds:
    running: print a color based on the value of running boolean

@author Amaury Brisou <py3status AT puzzledge.org>, lasers

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'0:00 / $0.00'}

running
{'color': '#FF0000', 'full_text': u'4:48 / $2.45'}
"""

import os
import time
SECONDS_IN_MIN = 60.0  # 60
SECONDS_IN_HOUR = 60 * SECONDS_IN_MIN  # 3600
SECONDS_IN_DAY = 24 * SECONDS_IN_HOUR  # 86400


class Py3status:
    """
    """
    # available configuration parameters
    button_reset = 3
    button_toggle = 1
    config_file = '~/.config/py3status/rate_counter.save'
    format = ('\?color=running \u2295[\?not_zero {days} days ]'
              '[\?not_zero {hours}:]{minutes}:{seconds} / ${total}')
    rate = 30
    tax = 1.02
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

    def post_config_hook(self):
        periods = [('*hours', 3600), ('*minutes', 60), ('*seconds', 1)]
        for name, cache in periods:
            if self.py3.format_contains(self.format, name):
                self.cache_timeout = cache
        self.config_file = os.path.expanduser(self.config_file)
        self.running = False
        self.saved_time = 0
        self.start_time = self._current_time
        self.rate = float(self.rate)
        self.tax = float(self.tax)
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
        if not self.running:
            self.saved_time = 0
            try:
                with open(self.config_file, 'w') as f:
                    f.write('0')
            except:
                pass

    def _start_timer(self):
        if not self.running:
            self.start_time = self._current_time - self.saved_time
            self.running = True

    def _stop_timer(self):
        if self.running:
            self.saved_time = self._current_time - self.start_time
            self.running = False

    def _toggle_timer(self):
        if self.running:
            self._stop_timer()
        else:
            self._start_timer()

    def kill(self):
        self._stop_timer()
        try:
            with open(self.config_file, 'w') as f:
                f.write(str(self.saved_time))
        except:
            pass

    def rate_counter(self):
        if self.running:
            cached_until = self.py3.time_in(self.cache_timeout)
            running_time = self._current_time - self.start_time
        else:
            cached_until = self.py3.CACHE_FOREVER
            running_time = self.saved_time

        days, hours, minutes, seconds = self._seconds_to_time(running_time)
        subtotal = self.rate * (running_time / SECONDS_IN_HOUR)
        total = subtotal * self.tax
        tax = total - subtotal
        total = '{:.2f}'.format(total)
        total_hours = '{:.2f}'.format(running_time / SECONDS_IN_HOUR)
        total_minutes = '{:.2f}'.format(running_time / SECONDS_IN_MIN)

        self.py3.threshold_get_color(int(self.running), 'running')

        return {
            'cached_until': cached_until,
            'full_text': self.py3.safe_format(
                self.format, {
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
                }
            )
        }

    def on_click(self, event):
        button = event['button']
        if button == self.button_toggle:
            self._toggle_timer()
        elif button == self.button_reset:
            self._reset_timer()
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
