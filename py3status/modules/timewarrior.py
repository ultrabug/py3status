r"""
Track your time with Timewarrior.

Timewarrior is a time tracking utility that offers simple stopwatch features
as well as sophisticated calendar-base backfill, along with flexible reporting.
See https://taskwarrior.org/docs/timewarrior for more information.

Configuration parameters:
    cache_timeout: refresh interval for this module, otherwise auto
        (default None)
    filter: specify interval and/or tag to filter (default '1day')
    format: display format for this module
        (default '[Timew {format_time}]|No Timew')
    format_datetime: specify strftime characters to format (default {})
    format_duration: display format for time duration
        (default '\?not_zero [{days}d ][{hours}:]{minutes}:{seconds}')
    format_tag: display format for tags (default '\?color=state_tag {name}')
    format_tag_separator: show separator if more than one (default ' ')
    format_time: display format for tracked times
        (default '[\?color=state_time [{format_tag} ]{format_duration}]')
    format_time_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use
        *(default {'state_tag': [(0, 'darkgray'), (1, 'darkgray')],
        'state_time': [(0, 'darkgray'), (1, 'degraded')]})*

Format placeholders:
    {format_time} format for tracked times
    {tracking} time tracking state, eg False, True

format_time placeholders:
    {state} time tracking state, eg False, True
    {format_tag} format for tags
    {format_duration} format for time duration
    {start} start date, eg 20171021T010203Z
    {end} end date, eg 20171021T010203Z

format_tag placeholders:
    {name} tag name, eg gaming, studying, gardening

format_datetime placeholders:
    key: start, end
    value: strftime characters, eg '%b %d' ----> 'Oct 06'

format_duration placeholders:
    {days} days
    {hours} hours
    {minutes} minutes
    {seconds} seconds

Color thresholds:
    format_time:
        state_time: print color based on the state of time tracking
    format_tag:
        state_tag:  print color based on the state of time tracking

Requires:
    timew: feature-rich time tracking utility

Recommendations:
    We can refresh a module using `py3-cmd` command.
    An excellent example of using this command in a function.

    ```
    ~/.{bash,zsh}{rc,_profile}
    ---------------------------
    function timew () {
        command timew "$@" && py3-cmd refresh timewarrior
    }
    ```

    With this, you can consider giving `cache_timeout` a much larger number,
    eg 3600 (an hour), so the module does not need to be updated that often.

Examples:
```
# show times matching the filter, see documentation for more filters
timewarrior {
    filter = ':day'           # filter times not in 24 hours of current day
    filter = '12hours'        # filter times not in 12 hours of current time
    filter = '5min'           # filter times not in 5 minutes of current time
    filter = '1sec'           # filter times not in 1 second of current time
    filter = '5pm to 11:59pm  # filter times not in 5pm to 11:59pm range
}

# intervals
timewarrior {
    # if you are printing other intervals too with '1day' filter or so,
    # then you may want to add this too for better bar readability
    format_time_separator = ', '

    # you also can change the thresholds with different colors
    thresholds = {
        'state_tag': [(0, 'darkgray'), (1, 'degraded')],
        'state_time': [(0, 'darkgray'), (1, 'degraded')],
    }
}

# cache_timeout
timewarrior {
    # auto refresh every 10 seconds when there is no active time tracking
    # auto refresh every second when there is active time tracking
    cache_timeout = None

    # refresh every minute when there is no active time tracking
    # refresh every second when there is active time tracking
    cache_timeout = 60

    # explicit refresh every 20 seconds when there is no active time tracking
    # explicit refresh every 5 seconds when there is active time tracking
    cache_timeout = (20, 5)
}

# add your snippets here
timewarrior {
    format = "..."
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'Timew '},
    {'full_text': 'gaming ', 'color': '#a9a9a9'},
    {'full_text': '15:02 ', 'color': '#a9a9a9'},
    {'full_text': 'studying ', 'color': '#a9a9a9'},
    {'full_text': '03:42', 'color': '#ffff00'}
]

no_tag
[
    {'full_text': 'Timew '},
    {'full_text': 'gardening ', 'color': '#a9a9a9'},
    {'full_text': '20:37', 'color': '#ffff00'}
]

no_timew
{'full_text': 'No Timew'}
"""

from json import loads as json_loads
import datetime as dt
from dateutil.relativedelta import relativedelta

STRING_NOT_INSTALLED = "not installed"
DATETIME = "%Y%m%dT%H%M%SZ"
STRING_INVALID_TIMEOUT = "invalid cache_timeout"


class Py3status:
    """"""

    # available configuration parameters
    cache_timeout = None
    filter = "1day"
    format = "[Timew {format_time}]|No Timew"
    format_datetime = {}
    format_duration = r"\?not_zero [{days}d ][{hours}:]{minutes}:{seconds}"
    format_tag = r"\?color=state_tag {name}"
    format_tag_separator = " "
    format_time = r"[\?color=state_time [{format_tag} ]{format_duration}]"
    format_time_separator = " "
    thresholds = {
        "state_tag": [(0, "darkgray"), (1, "darkgray")],
        "state_time": [(0, "darkgray"), (1, "degraded")],
    }

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {"minutes": ":02d", "seconds": ":02d"},
                    "format_strings": ["format_duration"],
                }
            ]
        }

    def post_config_hook(self):
        if not self.py3.check_commands("timew"):
            raise Exception(STRING_NOT_INSTALLED)

        if self.cache_timeout is None:
            self.sleep_timeout = 10
            self.cache_timeout = 0
        elif isinstance(self.cache_timeout, tuple):
            if len(self.cache_timeout) != 2:
                raise Exception(STRING_INVALID_TIMEOUT)
            self.sleep_timeout = self.cache_timeout[0]
            self.cache_timeout = self.cache_timeout[1]
        elif isinstance(self.cache_timeout, int):
            self.sleep_timeout = self.cache_timeout
            self.cache_timeout = 0

        self.timewarrior_command = "timew export"
        if self.filter:
            self.timewarrior_command += f" {self.filter}"

        self.init = {"datetimes": []}
        for word in ["start", "end"]:
            if (self.py3.format_contains(self.format_time, word)) and (
                word in self.format_datetime
            ):
                self.init["datetimes"].append(word)

        self.tracking = None
        self.thresholds_init = {}
        for name in ("format", "format_tag", "format_time"):
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def _get_timewarrior_data(self):
        return json_loads(self.py3.command_output(self.timewarrior_command))

    def _manipulate(self, data):
        new_time = []
        self.tracking = False

        for i, time in enumerate(data):
            time["index"] = len(data) - i
            time["state_time"] = "end" not in time

            # tags
            new_tag = []
            time["tags"] = time.get("tags", [])
            for tag_name in time["tags"]:
                tag_data = {"name": tag_name, "state_tag": time["state_time"]}
                for x in self.thresholds_init["format_tag"]:
                    if x in tag_data:
                        self.py3.threshold_get_color(tag_data[x], x)
                new_tag.append(self.py3.safe_format(self.format_tag, tag_data))

            format_tag_separator = self.py3.safe_format(self.format_tag_separator)
            format_tag = self.py3.composite_join(format_tag_separator, new_tag)

            time["format_tag"] = format_tag
            del time["tags"]

            # duraton
            if time["state_time"]:
                self.tracking = True
                end = dt.datetime.now(dt.timezone.utc)
            else:
                end = dt.datetime.strptime(time["end"], DATETIME)

            start = dt.datetime.strptime(time["start"], DATETIME)
            duration = relativedelta(end, start)

            time["format_duration"] = self.py3.safe_format(
                self.format_duration,
                {
                    "days": duration.days,
                    "hours": duration.hours,
                    "minutes": duration.minutes,
                    "seconds": duration.seconds,
                },
            )

            # datetime
            for word in self.init["datetimes"]:
                if word in time:
                    time[word] = self.py3.safe_format(
                        dt.datetime.strftime(
                            dt.datetime.strptime(time[word], DATETIME),
                            self.format_datetime[word],
                        )
                    )

            # time
            for x in self.thresholds_init["format_time"]:
                if x in time:
                    self.py3.threshold_get_color(time[x], x)

            new_time.append(self.py3.safe_format(self.format_time, time))

        format_time_separator = self.py3.safe_format(self.format_time_separator)
        format_time = self.py3.composite_join(format_time_separator, new_time)
        return format_time

    def timewarrior(self):
        timewarrior_data = self._get_timewarrior_data()
        format_time = self._manipulate(timewarrior_data)

        if self.tracking:
            cached_until = self.cache_timeout
        else:
            cached_until = self.sleep_timeout

        timew_data = {"format_time": format_time, "tracking": self.tracking}

        for x in self.thresholds_init["format"]:
            if x in timew_data:
                self.py3.threshold_get_color(timew_data[x], x)

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, timew_data),
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
