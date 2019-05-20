# -*- coding: utf-8 -*-
"""
Display system uptime.

Module has three modes:
"uptime" as in module "uptime" - 'up 1 days 18 hours 20 minutes'
"since" as in module "clock" - 'since Sun 15 Jan 2017 23:27:17 GMT'
"full" it's a combination of "uptime" and "since"
    'since Sun 15 Jan 2017 23:27:17 GMT up 1 days 18 hours 20 minutes'
By default used mode "uptime", and display a full equivalent to module "uptime"

Configuration parameters:
    format_since: format to use for the time, strftime directives such as `%H`
        can be used, this can be only a string.
        (default 'since %Y-%m-%d %H:%M [{name}]')
    format_uptime: display uptime format for this module
        (default 'up {days} days {hours} hours {minutes} minutes')
    format_zone: defines the timezones displayed. This must be a single string.
        (default '{Local}')
    view_mode: how uptime will be displayed. Default display uptime as in
        module uptime (default "uptime")

Format placeholders:
    {decades} decades
    {years}   years
    {weeks}   weeks
    {days}    days
    {hours}   hours
    {minutes} minutes
    {seconds} seconds
    {name} friendly timezone name eg `Buenos Aires`
    {timezone} full timezone name eg `America/Argentina/Buenos_Aires`

Note: If you don't use a placeholder, its value will be carried over
    to the next placeholder. For example, an uptime of 1 hour 30 minutes
    will give you 90 if {minutes} or 1:30 if {hours}:{minutes}.

Timezone are defined in the `format` using the TZ name in squiggly brackets eg
`{GMT}`, `{Portugal}`, `{Europe/Paris}`, `{America/Argentina/Buenos_Aires}`.

ISO-3166 two letter country codes eg `{de}` can also be used but if more than
one timezone exists for the country eg `{us}` the first one will be selected.

`{Local}` can be used for the local settings of your computer.

Note: Timezone are case sensitive

A full list of timezones can be found at
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

Requires:
    pytz: cross platform time zone library for python
    tzlocal: tzinfo object for the local timezone

Examples:
```
# show uptime without zeroes
uptime_adv {
    format_uptime = 'up [\?if=weeks {weeks} weeks ][\?if=days {days} days ]
        [\?if=hours {hours} hours ][\?if=minutes {minutes} minutes ]'
}

# show since in New York timezone
uptime_adv {
    view_mode = "since"
    format_zone = "Big Apple {America/New_York}"
    format_since = "since %Y-%m-%d %H:%M:%S"
}

```

With best regards to author module "uptime" Alexis "Horgix" Chotard
and to author module "clock" tobes

@author Volkov "BabyWolf" Semjon <Volkov.BabyWolf.Semjon@gmail.com>
@license BSD

SAMPLE OUTPUT
{'full_text': 'up 1 days 18 hours 20 minutes'}

Or
{'full_text': 'since Sun 15 Jan 2017 23:27:17 GMT'}

Or
{'full_text': 'since 15.05.2019 14:52:10 ↑ 0 days 10 hours 36 minutes'}

"""
from __future__ import division

import re
from datetime import datetime
from time import time
from collections import OrderedDict

import pytz
import tzlocal


class Py3status:
    """
    """

    # available configuration parameters
    format_since = "since %Y-%m-%d %H:%M [{name}]"
    format_uptime = "up {days} days {hours} hours {minutes} minutes"
    format_zone = "{Local}"
    view_mode = "uptime"

    def post_config_hook(self):
        if self.view_mode == "uptime":
            self._uptime_post_config_hook()
        elif self.view_mode == "since":
            self._since_post_config_hook()
        else:
            self.view_mode = "full"
            self._uptime_post_config_hook()
            self._since_post_config_hook()

    def _uptime_post_config_hook(self):
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
        for time_unit, seconds in periods:
            if self.py3.format_contains(self.format_uptime, time_unit):
                self.time_periods[time_unit] = seconds

    def _since_post_config_hook(self):
        # find any declared timezone eg {Europe/London}
        zonefmt = self.py3.get_placeholders_list(self.format_zone)
        self.name, self.zone = zonefmt[0], self._get_timezone(zonefmt[0])

        # workout how often in seconds we will need to do an update
        # to keep the display fresh
        time_format = re.sub(r"\{([^}]*)\}", "", self.format_since)
        time_format = time_format.replace("%%", "")
        if "%S" in time_format:
            # seconds
            time_delta = 1
        elif "%s" in time_format:
            # seconds since unix epoch start
            time_delta = 1
        elif "%T" in time_format:
            # seconds included in "%H:%M:%S"
            time_delta = 1
        elif "%c" in time_format:
            # Locale’s appropriate date and time representation
            time_delta = 1
        elif "%X" in time_format:
            # Locale’s appropriate time representation
            time_delta = 1
        else:
            time_delta = 60
        self.time_delta = time_delta

        # set our _fmt_strftime function depending on python version
        # @deprecated(version='4.0', reason="Support only python 3")
        if self.py3.is_python_2():
            self._fmt_strftime = self._fmt_strftime_py2
        else:
            self._fmt_strftime = self._fmt_strftime_py3

    # @deprecated(version='4.0', reason="Support only python 3")
    @staticmethod
    def _fmt_strftime_py2(fmt, t):
        """
        strftime for python 2
        """
        return t.strftime(fmt.encode("utf-8"))

    # @deprecated(version='4.0', reason="No more needed")
    @staticmethod
    def _fmt_strftime_py3(fmt, t):
        """
        strftime for python 3
        """
        return t.strftime(fmt)

    @staticmethod
    def _get_timezone(tz):
        """
        Find and return the time zone if possible
        """
        # special Local timezone
        if tz == "Local":
            try:
                return tzlocal.get_localzone()
            except pytz.UnknownTimeZoneError:
                return "?"

        # we can use a country code to get tz
        # FIXME this is broken for multi-timezone countries eg US
        # for now we just grab the first one
        if len(tz) == 2:
            try:
                zones = pytz.country_timezones(tz)
            except KeyError:
                return "?"
            tz = zones[0]

        # get the timezone
        try:
            zone = pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            return "?"
        return zone

    def uptime_adv(self):
        with open("/proc/uptime", "r") as f:
            time_up = int(float(f.readline().split()[0]))
            delta = time() - time_up

        if self.view_mode == "uptime":
            return self._uptime_adv_uptime(time_up, delta)
        elif self.view_mode == "since":
            return self._uptime_adv_since(delta)
        else:
            self.view_mode = "full"
            uptime_res = self._uptime_adv_uptime(time_up, delta)
            since_res = self._uptime_adv_since(delta)

            fulltext_up = fulltext_s = ""

            if self.py3.is_composite(since_res["full_text"]):
                for text in since_res["full_text"]:
                    fulltext_s += text["full_text"]

            if self.py3.is_composite(uptime_res["full_text"]):
                for text in uptime_res["full_text"]:
                    fulltext_up += text["full_text"]

            full_res = {
                "full_text": fulltext_s + fulltext_up,
                "cached_until": since_res["cached_until"],
            }
            return full_res

    def _uptime_adv_uptime(self, time_up, delta):
        uptime = {}
        timeout = 60
        for time_unit in self.time_periods:
            timeout = self.time_periods[time_unit]
            uptime[time_unit], time_up = divmod(time_up, timeout)

        return {
            "cached_until": self.py3.time_in(sync_to=timeout, offset=delta),
            "full_text": self.py3.safe_format(self.format_uptime, uptime),
        }

    def _uptime_adv_since(self, delta):
        uptime = {}
        name, zone = self.name, self.zone
        if zone == "?":
            uptime[name] = "?"
        else:
            t = datetime.fromtimestamp(delta, zone)

            format_time = self.format_since
            timezone = zone.zone
            tzname = timezone.split("/")[-1].replace("_", " ")

            format_time = self.py3.safe_format(
                format_time, dict(name=tzname, timezone=timezone)
            )

            if self.py3.is_composite(format_time):
                for item in format_time:
                    item["full_text"] = self._fmt_strftime(item["full_text"], t)
            else:
                format_time = self._fmt_strftime(format_time, t)
            uptime[name] = format_time

        # work out when we need to update
        timeout = self.py3.time_in(sync_to=self.time_delta)

        return {
            "cached_until": timeout,
            "full_text": self.py3.safe_format(self.format_zone, uptime),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
