"""
Display date and time.

This module allows one or more datetimes to be displayed.
All datetimes share the same format_time but can set their own timezones.
Timezones are defined in the `format` using the TZ name in squiggly brackets eg
`{GMT}`, `{Portugal}`, `{Europe/Paris}`, `{America/Argentina/Buenos_Aires}`.

ISO-3166 two letter country codes eg `{de}` can also be used but if more than
one timezone exists for the country eg `{us}` the first one will be selected.

`{Local}` can be used for the local settings of your computer.

Note: Timezones are case sensitive

A full list of timezones can be found at
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

Configuration parameters:
    block_hours: length of time period for all blocks in hours (default 12)
    blocks: a string, where each character represents time period
        from the start of a time period.
        (default '🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦')
    button_change_format: button that switches format used setting to None
        disables (default 1)
    button_change_time_format: button that switches format_time used. Setting
        to None disables (default 2)
    button_reset: button that switches display to the first timezone. Setting
        to None disables (default 3)
    cycle: If more than one display then how many seconds between changing the
        display (default 0)
    format: defines the timezones displayed. This can be a single string or a
        list.  If a list is supplied then the formats can be cycled through
        using `cycle` or by button click.  (default '{Local}')
    format_time: format to use for the time, strftime directives such as `%H`
        can be used this can be either a string or to allow multiple formats as
        a list.  The one used can be changed by button click.
        *(default ['[{name_unclear} ]%c', '[{name_unclear} ]%x %X',
        '[{name_unclear} ]%a %H:%M', '[{name_unclear} ]{icon}'])*
    locale: Override the system locale. Examples:
        when set to 'fr_FR' %a on Tuesday is 'mar.'.
        (default None)
    round_to_nearest_block: defines how a block icon is chosen. Examples:
        when set to True,  '13:14' is '🕐', '13:16' is '🕜' and '13:31' is '🕜';
        when set to False, '13:14' is '🕐', '13:16' is '🕐' and '13:31' is '🕜'.
        (default True)

Format placeholders:
    {icon} a character representing the time from `blocks`
    {name} friendly timezone name eg `Buenos Aires`
    {name_unclear} friendly timezone name eg `Buenos Aires` but is empty if
        only one timezone is provided
    {timezone} full timezone name eg `America/Argentina/Buenos_Aires`
    {timezone_unclear} full timezone name eg `America/Argentina/Buenos_Aires`
        but is empty if only one timezone is provided

Requires:
    pytz: cross platform time zone library for python
    tzlocal: tzinfo object for the local timezone

Examples:
```
# cycling through London, Warsaw, Tokyo
clock {
    cycle = 30
    format = ["{Europe/London}", "{Europe/Warsaw}", "{Asia/Tokyo}"]
    format_time = "{name} %H:%M"
}

# Show the time and date in New York
clock {
   format = "Big Apple {America/New_York}"
   format_time = "%Y-%m-%d %H:%M:%S"
}

# wall clocks
clock {
    format = "{Asia/Calcutta} {Africa/Nairobi} {Asia/Bangkok}"
    format_time = "{name} {icon}"
}
```

@author tobes
@license BSD

SAMPLE OUTPUT
{'full_text': 'Sun 15 Jan 2017 23:27:17 GMT'}

london
{'full_text': 'Thursday Feb 23 1:42 AM London'}
"""

import locale
import re
import time
from datetime import datetime

import pytz
import tzlocal

CLOCK_BLOCKS = "🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦"


class Py3status:
    """
    """

    # available configuration parameters
    block_hours = 12
    blocks = CLOCK_BLOCKS
    button_change_format = 1
    button_change_time_format = 2
    button_reset = 3
    cycle = 0
    format = "{Local}"
    format_time = [
        "[{name_unclear} ]%c",
        "[{name_unclear} ]%x %X",
        "[{name_unclear} ]%a %H:%M",
        "[{name_unclear} ]{icon}",
    ]
    locale = None
    round_to_nearest_block = True

    def post_config_hook(self):
        if self.locale is not None:
            locale.setlocale(locale.LC_TIME, self.locale)

        # Multiple clocks are possible that can be cycled through
        if not isinstance(self.format, list):
            self.format = [self.format]
        # if only one item we don't need to cycle
        if len(self.format) == 1:
            self.cycle = 0
        # find any declared timezones eg {Europe/London}
        self._fmts = set()
        for fmt in self.format:
            self._fmts.update(self.py3.get_placeholders_list(fmt))

        self.multiple_tz = len(self._fmts) > 1

        if not isinstance(self.format_time, list):
            self.format_time = [self.format_time]

        # workout how often in seconds we will need to do an update to keep the
        # display fresh
        self.time_deltas = []
        for format in self.format_time:
            format_time = re.sub(r"{([^}]*)}", "", format)
            format_time = format_time.replace("%%", "")
            if "%f" in format_time:
                # microseconds
                time_delta = 0
            elif "%S" in format_time:
                # seconds
                time_delta = 1
            elif "%s" in format_time:
                # seconds since unix epoch start
                time_delta = 1
            elif "%T" in format_time:
                # seconds included in "%H:%M:%S"
                time_delta = 1
            elif "%c" in format_time:
                # Locale’s appropriate date and time representation
                time_delta = 1
            elif "%X" in format_time:
                # Locale’s appropriate time representation
                time_delta = 1
            else:
                time_delta = 60
            self.time_deltas.append(time_delta)

        # If we have saved details we use them.
        saved_format = self.py3.storage_get("time_format")
        if saved_format in self.format_time:
            self.active_time_format = self.format_time.index(saved_format)
        else:
            self.active_time_format = 0

        saved_timezone = self.py3.storage_get("timezone")
        if saved_timezone in self.format:
            self.active = self.format.index(saved_timezone)
        else:
            self.active = 0

        # reset the cycle time
        self._cycle_time = time.perf_counter() + self.cycle

    def _get_timezone(self, tz):
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

    def _change_active(self, diff):
        self.active = (self.active + diff) % len(self.format)
        # reset the cycle time
        self._cycle_time = time.perf_counter() + self.cycle
        # save the active format
        timezone = self.format[self.active]
        self.py3.storage_set("timezone", timezone)

    def on_click(self, event):
        """
        Switch the displayed module or pass the event on to the active module
        """
        if event["button"] == self.button_reset:
            self._change_active(0)
        elif event["button"] == self.button_change_time_format:
            self.active_time_format += 1
            if self.active_time_format >= len(self.format_time):
                self.active_time_format = 0
            # save the active format_time
            time_format = self.format_time[self.active_time_format]
            self.py3.storage_set("time_format", time_format)
        elif event["button"] == self.button_change_format:
            self._change_active(1)

    def clock(self):

        # cycling
        if self.cycle and time.perf_counter() >= self._cycle_time:
            self._change_active(1)
            self._cycle_time = time.perf_counter() + self.cycle

        # update our times
        times = {}
        for name in self._fmts:
            zone = self._get_timezone(name)
            if zone == "?":
                times[name] = "?"
            else:
                t = datetime.now(zone)
                format_time = self.format_time[self.active_time_format]
                icon = None
                if self.py3.format_contains(format_time, "icon"):
                    # calculate the decimal hour
                    h = t.hour + t.minute / 60
                    if self.round_to_nearest_block:
                        h += self.block_hours / len(self.blocks) / 2
                    # make 12 hourly etc
                    h = h % self.block_hours
                    idx = int(h / self.block_hours * len(self.blocks))
                    icon = self.blocks[idx]

                timezone = zone.zone
                tzname = timezone.split("/")[-1].replace("_", " ")

                if self.multiple_tz:
                    name_unclear = tzname
                    timezone_unclear = timezone
                else:
                    name_unclear = ""
                    timezone_unclear = ""

                format_time = self.py3.safe_format(
                    format_time,
                    dict(
                        icon=icon,
                        name=tzname,
                        name_unclear=name_unclear,
                        timezone=timezone,
                        timezone_unclear=timezone_unclear,
                    ),
                )

                if self.py3.is_composite(format_time):
                    for item in format_time:
                        item["full_text"] = t.strftime(item["full_text"])
                else:
                    format_time = t.strftime(format_time)
                times[name] = format_time

        # work out when we need to update
        timeout = self.py3.time_in(sync_to=self.time_deltas[self.active_time_format])

        # if cycling we need to make sure we update when they are needed
        if self.cycle:
            cycle_timeout = self._cycle_time
            timeout = min(timeout, cycle_timeout)

        return {
            "full_text": self.py3.safe_format(self.format[self.active], times),
            "cached_until": timeout,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
