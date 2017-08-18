# -*- coding: utf-8 -*-
"""
Display upcoming calendar events from Google Calendar.

Configuration parameters:
    agenda_days: show calendar events for number of days (default 1)
    button_refresh: mouse button to refresh this module (default 2)
    cache_timeout: refresh interval for this module (default 3600)
    command: modify command to dictate the calendar events
        (default 'gcalcli agenda --tsv')
    format: display format for this module
        (default '{format_event}|\?color=event \u2687')
    format_event: display format for events
        (default '[\?if=is_first [\?if=is_date&color=date %a %b %-d ]]
        [\?if=is_time&color=time %-I:%M %p ][\?color=event {event}
        [\?if=is_multiple&color=multiple *]]')
    format_separator: show separator only if more than one (default ', ')
    remove: list of strings to remove from the output (default [])

Format placeholders:
    {format_event} format for events

format_event placeholders:
    {event}: scheduled event, eg Volleyball
    %?: a strftime character to be translated. See `man strftime`.
    is_date: a boolean based on calendar event data
    is_time: a boolean based on calendar event data
    is_first: a boolean based on calendar event data
    is_multiple: a boolean based on calendar event data

Color options:
    color_date: a date
    color_time: a time
    color_event: an event
    color_multiple: an indicator for multiple days

Requires:
    gcalcli: command line interface for google calendar

Examples:
```
# add colors
gcal {
    color_date = '#F3EA5F'
    color_time = '#2BD1FC'
    color_event = '#FF48C4'
    color_multiple= '#2BD1FC'
}

# show '7 PM' instead of '7:00 PM'
gcal {
    remove = [':00']
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'Thu Jul 20 Tacos, Volleyball'},
    {'full_text': '6:00 AM Garbage Pickup
    {'full_text': 'Sat Jul 22 6:05 PM Flight to Poland'},
]
"""

from datetime import datetime, timedelta
import re


STRING_NOT_INSTALLED = "gcalcli isn't installed"
DATE = '%Y-%m-%d'
TIME = '%H:%M'


class Py3status:
    """
    """
    # available configuration parameters
    agenda_days = 1
    button_refresh = 2
    cache_timeout = 3600
    command = 'gcalcli agenda --tsv'
    format = u'{format_event}|\?color=event \u2687'
    format_event = '[\?if=is_first [\?if=is_date&color=date %a %b %-d ]]' +\
        '[\?if=is_time&color=time %-I:%M %p ][\?color=event {event}' +\
        '[\?if=is_multiple&color=multiple *]]'
    format_separator = ', '
    remove = []

    def post_config_hook(self):
        if not self.py3.check_commands(self.command.split(' ', 1)[0]):
            raise Exception(STRING_NOT_INSTALLED)

        self.command += ' %s %s'
        self.first_run = True
        self.re = re.compile(r'(%s)' % '|'.join(self.remove))

    def _datetime(self, e, start=False, end=False):
        if start:
            return datetime.strptime(e['startdate'], DATE).date()
        elif end:
            return datetime.strptime(e['enddate'], DATE).date() - timedelta(days=1)
        else:
            return datetime.strptime(
                '%s %s' % (e['startdate'], e['starttime']), '%s %s' % (DATE, TIME))

    def _get_gcal_data(self):
        now = datetime.now()
        start = datetime.strftime(now, DATE)
        end = datetime.strftime(now + timedelta(days=self.agenda_days), DATE)
        return self.py3.command_output(self.command % (start, end))

    def _organize_data(self, data):
        new_data = []
        for line in data.splitlines():
            names = ['startdate', 'starttime', 'enddate', 'endtime', 'event']
            new_data.append(dict(zip(names, line.split('\t'))))

        return new_data

    def _manipulate_data(self, data):
        first_loop = True
        last_date = None
        new_data = []

        for e in data:
            e['is_date'] = True
            e['is_time'] = True
            e['is_first'] = False
            e['is_multiple'] = False

            if self._datetime(e, start=True) < self._datetime(e, end=True):
                e['is_multiple'] = True
            if first_loop:
                first_loop = False
                e['is_first'] = True
                last_date = e['startdate']
            elif last_date == e['startdate']:
                e['is_first'] = False
            else:
                e['is_first'] = True
                last_date = e['startdate']
            if e['starttime'] == e['endtime']:
                e['is_time'] = False

            obj = self._datetime(e)
            fmt = self.re.sub('', datetime.strftime(obj, self.format_event))
            new_data.append(self.py3.safe_format(fmt, {
                'event': e['event'],
                'is_date': e['is_date'],
                'is_time': e['is_time'],
                'is_first': e['is_first'],
                'is_multiple': e['is_multiple'],
            }))

        return new_data

    def gcal(self):
        cached_until = self.cache_timeout
        format_event = None

        if self.first_run:
            self.first_run = False
            cached_until = 0
        else:
            data = self._get_gcal_data()
            data = self._organize_data(data)
            data = self._manipulate_data(data)

            format_separator = self.py3.safe_format(self.format_separator)
            format_event = self.py3.composite_join(format_separator, data)

        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(
                self.format, {'format_event': format_event})
        }

    def on_click(self, event):
        button = event['button']
        if button != self.button_refresh:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
