# -*- coding: utf-8 -*-
"""
Track your time with Timewarrior.

Timewarrior is a time tracking utility that offers simple stopwatch features
as well as sophisticated calendar-base backfill, along with flexible reporting.
See https://taskwarrior.org/docs/timewarrior for more information.

It is also a command line tool. For this reason, the buttons are disabled by
default as a respect toward those who made and/or mastered timew and as a
suggestion toward users not familiar with the tool. Learning how to use timew
commands properly probably will always be the best way to track your time.

Configuration parameters:
    button_cancel: mouse button to cancel a running interval (default None)
    button_continue: mouse button to stop/continue an interval (default None)
    button_delete: mouse button to delete a specific interval (default None)
    button_stop: mouse button to stop/start an interval (default None)
    cache_timeout: refresh interval for this module (default 0)
    filter: specify interval and/or tag to filter (default None)
    format: display format for this module
        (default 'timew ({time})[ {format_time}]')
    format_datetime: specify strftime characters to format (default {})
    format_duration: display format for time duration
        *(default '\?not_zero [{years}y][{months}m][{weeks}w][{days}d]'
        '[\?soft  ][{hours}:]{minutes:02d}:{seconds:02d}')*
    format_tag: display format for tags (default '{name}')
    format_tag_separator: show separator if more than one (default ', ')
    format_time: display format for tracked times
        *(default '\?color=state [{format_tag}[\?soft  ]'
        '{format_duration}|\?show --:--]')*
    format_time_separator: show separator if more than one (default ', ')
    sleep_timeout: when a timew interval is running, this interval will be used
        to allow one to refresh constantly with time placeholders and/or
        to refresh every minute rather than every few seconds (default 20)
    thresholds: specify color thresholds to use
        (default [(0, 'darkgray'), (1, None)])

Control placeholders:
    {is_tracking} a tracking boolean based on timew data, eg False, True

Format placeholders:
    {time} number of tracked times
    {format_time} format for tracked times

format_time placeholders:
    {state} state, eg 0, 1
    {index} index number, eg 1
    {format_tag} format for tags
    {format_duration} format for time duration
    {start} start date, eg 20171021T010203Z
    {end} end date, eg 20171021T010203Z
    {tag} number of tags

format_tag placeholders:
    {index} index number, eg 1
    {name} tag name, eg lunch meeting

format_datetime placeholders:
    key: start, end
    value: strftime characters, eg '%b %d' ----> 'Oct 06'

format_duration placeholders:
    {years} years
    {months} months
    {weeks} weeks
    {days} days
    {hours} hours
    {minutes} minutes
    {seconds} seconds
    {microseconds} microseconds

Color thresholds:
    format:
        time:       print color based on number of tracked times
    format_time:
        time_index: print color based on tracked time index
        tag:        print color based on number of tags
    format_tag:
        tag_index:  print color based on tag index

Requires:
    timew: feature-rich time tracking utility

Recommendations:
    We can refresh a module using `py3-cmd` command.
    An excellent example of using this command in a function.

    | ~/.{bash,zsh}{rc,_profile}
    | ---------------------------
    | function timew () {
    |     command timew "$@" && py3-cmd refresh timewarrior
    | }

    With this, you can consider giving `sleep_timeout` a much larger number,
    eg 3600 (an hour), as this module would no longer need to be updated often
    since it now gets updated immediately after any issued `timew` command too.

Examples:
```
# show times matching the filter, see documentation for more filters
timewarrior {
    filter = ':day'           # filter times not in 24 hours of current day
    filter = '12hours'        # filter times not in 12 hours of current time
    filter = '12hours'        # filter times not in 12 hours of current time
    filter = '5pm to 11:59pm  # filter times not in 5pm to 11:59pm range
}

# show latest time only
timewarrior {
    format = '{format_time}|\?show No time'
    format_time = '\?if=state&color=state [{format_tag}[\?soft  ]'
    format_time += '{format_duration}|\?show --:--]'

    # alternative, {time} will print one instead of total tracked times
    filter = '1min'  # filter everything but current interval
}

# add rainbow threshold
timewarrior {
    thresholds = [
        (0, '#bababa'),
        (1, '#ffb3ba'),
        (2, '#ffdfba'),
        (3, '#ffffba'),
        (4, '#baefba'),
        (5, '#baffc9'),
        (6, '#bae1ff'),
        (7, '#bab3ff')
    ]
}

# show rainbow times
timewarrior {
    format_time = '\?color=time_index [{format_tag}]'
    format_time += '[\?soft  ][{format_duration}]'
}

# show rainbow number of tracked times
timewarrior {
    format = '\?color=time {time} times'
}

# replace tags with symbols
timewarrior {
    format_time = '{format_tag}'
    format_tag = '[\?if=name=meeting&color=good M|'
    format_tag += '[\?if=name=gym&color=degraded G|'
    format_tag += '\?color=degraded {name}]]'
}

# add buttons
timewarrior {
    button_stop = 1      # stops tracking time
    button_cancel = 3    # if there is an open interval, it is abandoned
    button_continue = 8  # resumes tracking of closed intervals
    button_delete = 9    # delete an interval
}

# add your snippets here
timewarrior {
    format = '...'
}
```

@author lasers

SAMPLE OUTPUT
{'full_text': 'timew (1) 00:33'}

many_times
[
    {'full_text': 'timew (5) '}, {'color': '#a9a9a9', 'full_text': '00:04'},
    {'full_text': ', '}, {'color': '#a9a9a9', 'full_text': '05:07'},
    {'full_text': ', '}, {'color': '#a9a9a9', 'full_text': '19:03'},
    {'full_text': ', '}, {'color': '#a9a9a9', 'full_text': '1:15:02'},
[

start_and_tag
[
    {'full_text': 'timew (3) 00:33'}, {'full_text': ', '},
    {'color': '#a9a9a9', 'full_text': '33:03'}, {'full_text': ', '},
    {'color': '#a9a9a9', 'full_text': 'lunch meeting 5:50'},
    {'full_text': ', --:--'},
]
"""

from pytz import utc
from json import loads
from datetime import datetime
from dateutil.relativedelta import relativedelta

STRING_NOT_INSTALLED = 'not installed'
DATETIME = '%Y%m%dT%H%M%SZ'


class Py3status:
    """
    """
    button_cancel = None
    button_continue = None
    button_delete = None
    button_stop = None
    cache_timeout = 0
    filter = None
    format = 'timew ({time})[ {format_time}]'
    format_datetime = {}
    format_duration = ('\?not_zero [{years}y][{months}m][{weeks}w][{days}d]'
                       '[\?soft  ][{hours}:]{minutes:02d}:{seconds:02d}')
    format_tag = '{name}'
    format_tag_separator = ', '
    format_time = ('\?color=state [{format_tag}[\?soft  ]'
                   '{format_duration}|\?show --:--]')
    format_time_separator = ', '
    sleep_timeout = 20
    thresholds = [(0, 'darkgray'), (1, None)]

    def post_config_hook(self):
        if not self.py3.check_commands('timew'):
            raise Exception(STRING_NOT_INSTALLED)

        self.timewarrior_command = 'timew export'
        if self.filter:
            self.timewarrior_command += ' {}'.format(self.filter)

        self.init = {'datetimes': []}
        for word in ['start', 'end']:
            if (self.py3.format_contains(self.format_time, word)) and (
                    word in self.format_datetime):
                self.init['datetimes'].append(word)
        self.is_tracking = None

    def _get_timewarrior_data(self):
        return loads(self.py3.command_output(self.timewarrior_command))

    def _manipulate(self, data):
        new_time = []
        self.is_tracking = False

        for time_index, time in zip(range(len(data), -1, -1), data):
            time['time_index'] = time_index
            new_tag = []

            if 'tags' in time:
                for index, x in enumerate(time['tags'], 1):
                    new_tag.append(self.py3.safe_format(
                        self.format_tag, {'name': x, 'index': index}))
                    if self.thresholds:
                        self.py3.threshold_get_color(index, 'tag_index')
                del time['tags']
            time['tag'] = len(new_tag)
            time['format_tag'] = self.py3.composite_join(
                self.py3.safe_format(self.format_tag_separator), new_tag)

            # duration
            if 'end' in time:
                end = datetime.strptime(time['end'], DATETIME)
                time['state'] = 0
            else:
                self.is_tracking = True
                end = datetime.now(utc).utcnow()
                time['state'] = 1

            start = datetime.strptime(time['start'], DATETIME)
            duration = relativedelta(end, start)

            time['format_duration'] = self.py3.safe_format(
                self.format_duration, {
                    'years': duration.years,
                    'months': duration.months,
                    'weeks': duration.weeks,
                    'days': duration.days,
                    'hours': duration.hours,
                    'minutes': duration.minutes,
                    'seconds': duration.seconds,
                    'microseconds': duration.microseconds
                }
            )

            for word in self.init['datetimes']:
                if word in time:
                    time[word] = self.py3.safe_format(datetime.strftime(
                        datetime.strptime(time[word], DATETIME),
                        self.format_datetime[word]))

            for k, v in time.items():
                if isinstance(v, (int, float)):
                    self.py3.threshold_get_color(v, k)

            format_time = self.py3.safe_format(self.format_time, time)
            self.py3.composite_update(
                format_time, {'index': 'timew/{}'.format(time_index)}
            )
            new_time.append(format_time)

        format_time_separator = self.py3.safe_format(self.format_time_separator)
        format_time = self.py3.composite_join(format_time_separator, new_time)
        return format_time

    def timewarrior(self):
        timewarrior_data = self._get_timewarrior_data()
        cached_until = self.sleep_timeout
        count_time = len(timewarrior_data)
        format_time = self._manipulate(timewarrior_data)

        if self.is_tracking:
            cached_until = self.cache_timeout

        if self.thresholds:
            self.py3.threshold_get_color(count_time, 'time')

        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(
                self.format, {
                    'format_time': format_time,
                    'time': count_time,
                }
            )
        }

    def on_click(self, event):
        button = event['button']
        action = index = None
        if 'timew' in format(event['index']):
            index = event['index'].split('/')[-1]
        if button == self.button_delete:
            if index:
                action = 'delete @{}'.format(index)
        elif button == self.button_cancel:
            if self.is_tracking:
                action = 'cancel'
        elif button in [self.button_continue, self.button_stop]:
            if self.is_tracking:
                action = 'stop'
            else:
                if button == self.button_continue:
                    action = 'continue'
                    if index:
                        action += ' @{}'.format(index)
                elif button == self.button_stop:
                    action = 'start'
        if action:
            self.py3.command_run('timew {}'.format(action))
        elif self.is_tracking:
            self.py3.prevent_refresh()


if __name__ == '__main__':
    from py3status.module_test import module_test
    module_test(Py3status)
