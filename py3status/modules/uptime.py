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

Note: If you don't use a placeholder, its value will be carried over
    to the next placeholder. For example, an uptime of 1 hour 30 minutes
    will give you 90 if {minutes} or 1:30 if {hours}:{minutes}.

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

@author Alexis "Horgix" Chotard <alexis.horgix.chotard@gmail.com>
@license BSD

SAMPLE OUTPUT
{'full_text': 'up 1 days 18 hours 20 minutes'}
"""

from time import time
from collections import OrderedDict


class Py3status:
    """
    """

    # available configuration parameters
    format = "up {days} days {hours} hours {minutes} minutes"

    def post_config_hook(self):
        self.time_periods = OrderedDict()
        periods = [
            ("decades", 315360000),
            ("years", 31536000),
            ("weeks", 604800),
            ("days", 86400),
            ("hours", 3600),
            ("minutes", 60),
            ("seconds", 1),
        ]
        for unit, second in periods:
            if self.py3.format_contains(self.format, unit):
                self.time_periods[unit] = second

    def uptime(self):
        with open("/proc/uptime", "r") as f:
            up = int(float(f.readline().split()[0]))
            offset = time() - up

        uptime = {}
        for unit in self.time_periods:
            interval = self.time_periods[unit]
            uptime[unit], up = divmod(up, interval)

        return {
            "cached_until": self.py3.time_in(sync_to=interval, offset=offset),
            "full_text": self.py3.safe_format(self.format, uptime),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
