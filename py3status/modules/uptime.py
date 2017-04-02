# -*- coding: utf-8 -*-
"""
Display system uptime.

Configuration parameters:
    format: display format for this module
        (default 'up {days} days {hours} hours {minutes} minutes')

Format placeholders:
    {decades} decades
    {years}   years
    {weeks}   weeks
    {days}    days
    {hours}   hours
    {minutes} minutes
    {seconds} seconds

Note: If you don't use one of the placeholders, the value will be carried over
    to the next unit. For example, given an uptime of 1h 30min:
    If you use {minutes} as your only placeholder, then its value will be 90.
    If you use {hours} and {minutes}, then its values will be 1 and 30, respectively.

Examples:
```
# show uptime without zeroes
uptime {
    format = 'up [\?if=weeks {weeks} weeks ][\?if=days {days} days ]
        [\?if=hours {hours} hours ][\?if=minutes {minutes} minutes ]'
}

# show uptime in multiple formats using group module
group uptime {
    format = "up {output}"
    uptime {
        format = '[\?if=weeks {weeks} weeks ][\?if=days {days} days ]
            [\?if=hours {hours} hours ][\?if=minutes {minutes} minutes]'
    }
    uptime {
        format = '[\?if=weeks {weeks}w ][\?if=days {days}d ]
            [\?if=hours {hours}h ][\?if=minutes {minutes}m]'
    }
    uptime {
        format = '[\?if=days {days}, ][\?if=hours {hours}:]
            [\?if=minutes {minutes:02d}]'
    }
}
```

@author Alexis "Horgix" Chotard <alexis.horgix.chotard@gmail.com>, tobes, lasers
@license BSD

SAMPLE OUTPUT
{'full_text': 'up 1 days 18 hours 20 minutes'}
"""

from time import time


class Py3status:
    """
    """
    # available configuration parameters
    format = 'up {days} days {hours} hours {minutes} minutes'

    def post_config_hook(self):
        self._decades = self.py3.format_contains(self.format, 'decades')
        self._years = self.py3.format_contains(self.format, 'years')
        self._weeks = self.py3.format_contains(self.format, 'weeks')
        self._days = self.py3.format_contains(self.format, 'days')
        self._hours = self.py3.format_contains(self.format, 'hours')
        self._minutes = self.py3.format_contains(self.format, 'minutes')
        self._seconds = self.py3.format_contains(self.format, 'seconds')

    def uptime(self):
        # Units will be computed from bare seconds since timedelta only
        # provides .days and .seconds anyway. Getting rid of the seconds
        # part. Keeping the floating point part would make divmod return
        # floats, and thus would require days/hours/minutes/seconds to be
        # casted to int before formatting, which would be dirty to handle
        # since we can't cast None to int.
        with open('/proc/uptime', 'r') as f:
            up = int(float(f.readline().split()[0]))
            offset = time() - up

        cache_timeout = decades = years = weeks = days = hours = minutes = seconds = 0

        # Decades
        if self._decades:
            decades, up = divmod(up, 315360000)  # 10 years -> decade
            cache_timeout = 315360000
        # Years
        if self._years:
            years, up = divmod(up, 31536000)  # 365 days -> year
            cache_timeout = 31536000
        # Weeks
        if self._weeks:
            weeks, up = divmod(up, 604800)  # 7 days -> week
            cache_timeout = 604800
        # Days
        if self._days:
            days, up = divmod(up, 86400)  # 24 hours -> day
            cache_timeout = 86400
        # Hours
        if self._hours:
            hours, up = divmod(up, 3600)  # 60 minutes -> hour
            cache_timeout = 3600
        # Minutes
        if self._minutes:
            minutes, up = divmod(up, 60)  # 60 seconds -> minute
            cache_timeout = 60
        # Seconds
        if self._seconds:
            seconds = up  # 1000000000 nanoseconds -> second
            cache_timeout = 1

        uptime = self.py3.safe_format(self.format, dict(
            decades=decades, years=years, weeks=weeks, days=days,
            hours=hours, minutes=minutes, seconds=seconds))

        return {
            'cached_until': self.py3.time_in(sync_to=cache_timeout, offset=offset),
            'full_text': uptime
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
