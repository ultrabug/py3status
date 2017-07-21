# -*- coding: utf-8 -*-
"""
Display week calendar.

Make your days more and colorful. This module comes with a toggle to turn off
all days except today so you can concentrate better on this day.

Configuration parameters:
    button_refresh: mouse button to refresh this module (default 2)
    button_toggle: mouse button to toggle between states (default 1)
    cache_timeout: refresh interval for this module (default 3600)
    first_weekday: First week day. 0-6 is Monday-Sunday (default 6)
    format: display format for this module (default '%a %b {format_datetime}')
    format_separator: separator between datetime (default ' ')
    format_today: display format for today (default '\?color=good %-d')
    format_weekday: display format for week days (default '%-d')
    format_weekend: display format for weekend days (default '%-d')
    is_toggled: toggle to turn off all days except today (default False)

Format* conversion (excluding separator):
    %a  locale's abbreviated weekday name (e.g., Sun)
    %b  locale's abbreviated month name (e.g., Jan)
    %d  day of month (e.g., range 01 to 31)
    %Y  year (e.g., range 2017 and above)
    %?  strftime parameters to be translated. See `man strftime'.

Examples:
```
# show color only inside the toggled container
weekcal {
    format_today = '\?if=is_toggled %d|\?color=good %d'
}
# show datetime in middle instead of left
weekcal {
    format = '{format_datetime}'
    format_today = '\?color=good %a %b %d'
}
# show colorized weekend days
weekcal {
    format = '{format_datetime}'
    format_weekend = '\?color=#999 %d'
}
# show clock
weekcal {
    format = '%a %b {format_datetime} %-I:%M %p'
    cache_timeout = 60
    is_toggled = True
}
```

SAMPLE OUTPUT
[
    {'color': '#FFFFFF', 'full_text': 'Wed Apr 23 24 25 '},
    {'color': '#00FF00', 'full_text': '23 '},
    {'color': '#FFFFFF', 'full_text': '27 28 29'},
    {'color': '#FFFFFF', 'full_text': 'Wed Apr ', 'separator': True},
    {'color': '#00FF00', 'full_text': '26 '},
]

custom-1
[
    {'color': '#FFFFFF', 'full_text': 'Wed Apr 24 25'},
    {'color': '#00FF00', 'full_text': '26 '},
    {'color': '#FFFFFF', 'full_text': '27 28 '},
    {'color': '#FFFF00', 'full_text': '29 30'},
    {'color': '#FFFFFF', 'full_text': 'Wed Apr ', 'separator': True},
    {'color': '#00FF00', 'full_text': '26 '},
]

custom-2
[
    {'color': '#999999', 'full_text': '23 '},
    {'color': '#FFFFFF', 'full_text': '24 25 '},
    {'color': '#00FF00', 'full_text': 'Wed Apr 26 '},
    {'color': '#FFFFFF', 'full_text': '27 28 '},
    {'color': '#999999', 'full_text': '29'},
    {'color': '#00FF00', 'full_text': 'Wed Apr 26', 'separator': True},
]

custom-3
[
    {'color': '#FFFFFF', 'full_text': 'Wed Apr '},
    {'color': '#999999', 'full_text': '23 24 25 '},
    {'color': '#FFFFFF', 'full_text': '26 '},
    {'color': '#999999', 'full_text': '27 28 29'},
    {'color': '#FFFFFF', 'full_text': 'Wed Apr 26', 'separator': True},
]
"""

from calendar import Calendar
from datetime import date, datetime, timedelta


class Py3status:
    """
    """
    # available configuration parameters
    button_refresh = 2
    button_toggle = 1
    cache_timeout = 3600
    first_weekday = 6
    format = '%a %b {format_datetime}'
    format_separator = ' '
    format_today = '\?color=good %-d'
    format_weekday = '%-d'
    format_weekend = '%-d'
    is_toggled = False

    def post_config_hook(self):
        self.calendar = Calendar(self.first_weekday)

    def weekcal(self):
        today = date.today()
        data = []
        nextweek = False

        weekdays = self.calendar.iterweekdays()
        for weekday_number in weekdays:
            if weekday_number == 0 and self.first_weekday != 0:
                nextweek = True
            if nextweek and today.weekday() >= self.first_weekday:
                weekday_number += 7
            elif not nextweek and today.weekday() < self.first_weekday:
                weekday_number -= 7

            weekday_offset = today.weekday() - weekday_number
            weekday_delta = timedelta(days=weekday_offset)
            weekday = today - weekday_delta
            _format = None

            if weekday == today:
                _format = self.format_today
            elif not self.is_toggled:
                if weekday.weekday() <= 4:
                    _format = self.format_weekday
                else:
                    _format = self.format_weekend
            if _format:
                data.append(self.py3.safe_format(weekday.strftime(_format)))

        format_datetime = self.py3.composite_join(self.format_separator, data)
        _format = datetime.now().strftime(self.format)

        return {
            'cached_until': self.py3.time_in(sync_to=self.cache_timeout),
            'full_text': self.py3.safe_format(
                _format, {'format_datetime': format_datetime})
        }

    def on_click(self, event):
        button = event['button']
        if button == self.button_toggle:
            self.is_toggled = not self.is_toggled
        elif button != self.button_refresh:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
