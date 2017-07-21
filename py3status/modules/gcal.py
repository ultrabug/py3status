# -*- coding: utf-8 -*-
"""
Display upcoming calendar events from Google Calendar.

Configuration parameters:
    button_refresh: mouse button to refresh this module (default 2)
    cache_timeout: refresh interval for this module (default 3600)
    command: modify command to dictate the calendar events
        (default 'gcalcli agenda --nocolor')
    days: show calendar events for number of days (default 1)
    format: display format for this module (default '{format_event}')
    format_event: display format for events
        (default '[\?if=is_date %a %b %d ][\?if=is_time %-I:%M %p ]{event}')
    format_separator: show separator only if more than one (default ', ')
    remove: list of strings to remove from the output (default [])

Format placeholders:
    {format_event} format for events

format_event placeholders:
    {event} scheduled event eg Volleyball
    %?  strftime characters to be translated. See `man strftime`.
    is_time: a boolean based on calendar event data
    is_date: a boolean based on calendar event data

Requires:
    gcalcli: Google Calendar CLI

Examples:
```
# add colors and optionally customize timedate
gcal {
    format_event = '[\?if=is_date&color=#F3EA5F %a %b %d ]'
    format_event += '[\?if=is_time&color=#2BD1FC %-I:%M %p ]'
    format_event += '[\?color=#FF48C4 {event}]'
}

# show '7 PM'
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
GCAL_AGENDA = '%Y%m%d'
GCAL_DATE = '%a %b %d'
GCAL_TIME = '%I:%M%p'
GCAL_YEAR = '%Y'


class Py3status:
    """
    """
    # available configuration parameters
    button_refresh = 2
    cache_timeout = 3600
    command = 'gcalcli agenda --nocolor'
    days = 1
    format = u'{format_event}'
    format_event = '[\?if=is_date %a %b %d ][\?if=is_time %-I:%M %p ]{event}'
    format_separator = ', '
    remove = []

    def post_config_hook(self):
        self.first_run = True
        self.command = self.command + ' %s %s'
        if not self.py3.check_commands(self.command.split(' ', 1)[0]):
            raise Exception(STRING_NOT_INSTALLED)

        remove = '|'.join(self.remove)
        self.re = re.compile(r'(' + remove + ')')

    def _get_gcal_data(self):
        now = datetime.now()
        self.tempfix_year = now.year
        start = datetime.strftime(now, GCAL_AGENDA)
        end = datetime.strftime(now + timedelta(days=self.days), GCAL_AGENDA)
        return self.py3.command_output(self.command % (start, end))

    def _organize_data(self, data):
        new_data = []
        for line in data.splitlines():
            if line.rstrip():
                if line == 'No Events Found...':
                    break
                temporary = {
                    'date': line[:10].strip(),
                    'time': line[10:20].strip(),
                    'event': line[20:].strip(),
                    'year': self.tempfix_year,
                }
                new_data.append({k: v for k, v in temporary.items() if v})

        return new_data

    def _manipulate_data(self, data):
        new_data = []
        for e in data:
            obj, is_date, is_time, _fmt = None, False, False, self.format_event
            if 'date' in e:
                is_date = True
                if 'time' in e:
                    is_time = True
                    obj = datetime.strptime('%s %s %s' % (
                        e['date'], e['time'], e['year']), '%s %s %s' % (
                            GCAL_DATE, GCAL_TIME, GCAL_YEAR))
                else:
                    obj = datetime.strptime('%s %s' % (
                        e['date'], e['year']), '%s %s' % (
                        GCAL_DATE, GCAL_YEAR))
            elif 'time' in e:
                is_time = True
                obj = datetime.strptime('%s %s' % (
                    e['time'], e['year']), '%s %s' % (
                    GCAL_TIME, GCAL_YEAR))
            if obj:
                _fmt = self.re.sub('', datetime.strftime(obj, _fmt))

            new_data.append(self.py3.safe_format(_fmt, {'event': e.get(
                'event'), 'is_date': is_date, 'is_time': is_time}))

        return new_data

    def gcal(self):
        """
        """
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
    config = {'format': '{format_event}|No Events'}
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
