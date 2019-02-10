# -*- coding: utf-8 -*-
"""
Display time spent and calculate the price of your service.

Configuration parameters:
    cache_timeout: how often to update in seconds (default 5)
    config_file: file path to store the time already spent
        and restore it the next session
        (default '~/.i3/py3status/counter-config.save')
    format: output format string
        (default 'Time: {days} day {hours}:{mins:02d} Cost: {total}')
    format_money: output format string
        (default '{price}$')
    hour_price: your price per hour (default 30)
    tax: tax value (1.02 = 2%) (default 1.02)

Format placeholders:
    {days} The number of whole days in running timer
    {hours} The remaining number of whole hours in running timer
    {mins} The remaining number of whole minutes in running timer
    {secs} The remaining number of seconds in running timer
    {subtotal} The subtotal cost (time * rate)
    {tax} The tax cost, based on the subtotal cost
    {total} The total cost (subtotal + tax)
    {total_hours} The total number of whole hours in running timer
    {total_mins} The total number of whole minutes in running timer

format_money placeholders:
    {price} numeric value of money

Color options:
    color_running: Running, default color_good
    color_stopped: Stopped, default color_bad

@author Amaury Brisou <py3status AT puzzledge.org>

SAMPLE OUTPUT
{'color': '#FF0000', 'full_text': u'Time: 0 day 0:00 Cost: 0.13$'}
"""


import os
import time


# No "magic numbers"
SECS_IN_MIN = 60.0
SECS_IN_HOUR = 60 * SECS_IN_MIN  # 3600
SECS_IN_DAY = 24 * SECS_IN_HOUR  # 86400


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    config_file = "~/.i3/py3status/counter-config.save"
    format = "Time: {days} day {hours}:{mins:02d} Cost: {total}"
    format_money = "{price}$"
    hour_price = 30
    tax = 1.02

    def post_config_hook(self):
        self.config_file = os.path.expanduser(self.config_file)
        self.running = False
        self.saved_time = 0
        self.start_time = self.current_time
        try:
            # Use file to refer to the file object
            with open(self.config_file) as file:
                self.saved_time = float(file.read())
        except:  # noqa e722 // (IOError, FileNotFoundError):  # py2/py3
            pass

    @property
    def current_time(self):
        """Get the current time.

        Using a helper property to make it easy to keep consitency.
        """
        return time.time()

    @staticmethod
    def secs_to_dhms(time_in_secs):
        """Convert seconds to days, hours, minutes, seconds.

        Using days as the largest unit of time.  Blindly using the days in
        `time.gmtime()` will fail if it's more than one month (days > 31).
        """
        days = int(time_in_secs / SECS_IN_DAY)
        remaining_secs = time_in_secs % SECS_IN_DAY
        hours = int(remaining_secs / SECS_IN_HOUR)
        remaining_secs = remaining_secs % SECS_IN_HOUR
        mins = int(remaining_secs / SECS_IN_MIN)
        secs = int(remaining_secs % SECS_IN_MIN)
        return days, hours, mins, secs

    def _start_timer(self):
        if not self.running:
            self.start_time = self.current_time - self.saved_time
            self.running = True

    def _stop_timer(self):
        if self.running:
            self.saved_time = self.current_time - self.start_time
            self.running = False

    def _toggle_timer(self):
        if self.running:
            self._stop_timer()
        else:
            self._start_timer()

    def kill(self):
        self._stop_timer()
        with open(self.config_file, "w") as f:
            f.write(str(self.saved_time))

    def on_click(self, event):
        if event["button"] == 1:
            self._toggle_timer()
        elif event["button"] == 3:
            self._reset()

    def _reset(self):
        if not self.running:
            self.saved_time = 0.0
            with open(self.config_file, "w") as f:
                f.write("0")

    def rate_counter(self):
        running_time = 0.0
        if self.running:
            color = self.py3.COLOR_RUNNING or self.py3.COLOR_GOOD
            running_time = self.current_time - self.start_time
        else:
            color = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
            running_time = self.saved_time

        days, hours, mins, secs = self.secs_to_dhms(running_time)
        subtotal = float(self.hour_price) * (running_time / SECS_IN_HOUR)
        total = subtotal * float(self.tax)
        subtotal_cost = self.py3.safe_format(
            self.format_money, {"price": "%.2f" % subtotal}
        )
        total_cost = self.py3.safe_format(self.format_money, {"price": "%.2f" % total})
        tax_cost = self.py3.safe_format(
            self.format_money, {"price": "%.2f" % (total - subtotal)}
        )
        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": color,
            "full_text": self.py3.safe_format(
                self.format,
                dict(
                    days=days,
                    hours=hours,
                    mins=mins,
                    secs=secs,
                    total_hours=running_time // SECS_IN_HOUR,
                    total_mins=running_time // SECS_IN_MIN,
                    subtotal=subtotal_cost,
                    total=total_cost,
                    tax=tax_cost,
                ),
            ),
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
