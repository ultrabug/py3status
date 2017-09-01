# -*- coding: utf-8 -*-
"""
Display calculated time spent and costs.

Configuration parameters:
    button_reset: mouse button to reset the timer (default 3)
    button_toggle: mouse button to toggle the timer (default 1)
    cache_timeout: refresh interval for this module (default 5)
    config_file: specify a file to save time between sessions
        (default '~/.i3/py3status/counter-config.save')
    format: display format for this module
        (default '[\?not_zero {days} days ][\?not_zero {hours}:]
        {minutes:02d}:{seconds:02d} / ${total:.2f}')
    rate: specify the hourly pay rate to use (default 30)
    tax: specify the tax value to use, 1.02 is 2% (default 1.02)

Format placeholders:
    {days} The number of whole days in running timer
    {hours} The remaining number of whole hours in running timer
    {minutes} The remaining number of whole minutes in running timer
    {rate} The user inputted hourly rate
    {seconds} The remaining number of seconds in running timer
    {subtotal} The subtotal cost (time * rate)
    {tax} The tax cost, based on the subtotal cost
    {total} The total cost (subtotal + tax)
    {total_hours} The total number of whole hours in running timer
    {total_minutes} The total number of whole minutes in running timer

Color options:
    color_running: Running, defaults to color_good
    color_stopped: Stopped, defaults to color_bad

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
    cache_timeout = 5
    config_file = '~/.i3/py3status/counter-config.save'
    format = '[\?not_zero {days} days ][\?not_zero {hours}:]' +\
        '{minutes:02d}:{seconds:02d} / ${total:.2f}'
    rate = 30
    tax = 1.02

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
        self.config_file = os.path.expanduser(self.config_file)
        self.running = False
        self.saved_time = 0
        self.start_time = self._current_time
        self.color_running = self.py3.COLOR_RUNNING or self.py3.COLOR_GOOD
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
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
        minutes = int(remaining_seconds / SECONDS_IN_MIN)
        seconds = int(remaining_seconds % SECONDS_IN_MIN)
        return days, hours, minutes, seconds

    def _reset_timer(self):
        if not self.running:
            self.saved_time = 0.0
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
        cached_until = self.py3.CACHE_FOREVER
        color = self.color_stopped
        running_time = self.saved_time

        if self.running:
            cached_until = self.py3.time_in(self.cache_timeout)
            color = self.color_running
            running_time = self._current_time - self.start_time

        days, hours, minutes, seconds = self._seconds_to_time(running_time)
        subtotal = float(self.rate) * (running_time / SECONDS_IN_HOUR)
        total = subtotal * float(self.tax)

        return {
            'cached_until': cached_until,
            'color': color,
            'full_text': self.py3.safe_format(
                self.format, {
                    'days': days,
                    'hours': hours,
                    'minutes': minutes,
                    'rate': self.rate,
                    'seconds': seconds,
                    'subtotal': subtotal,
                    'tax': total - subtotal,
                    'total': total,
                    'total_hours': running_time // SECONDS_IN_HOUR,
                    'total_minutes': running_time // SECONDS_IN_MIN,
                }
            )
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
