# -*- coding: utf-8 -*-
"""
Display upcoming events from Google Calendar.

Configuration parameters:
    arguments: additional arguments for the gcalcli command (default [])
    button_next: mouse button to focus next event (default None)
    button_open: mouse button to open calendar or event url (default None)
    button_previous: mouse button to focus previous event (default None)
    button_refresh: mouse button to refresh this module (default None)
    button_reset: mouse button to reset the scrolling (default None)
    cache_timeout: refresh interval for this module (default 3600)
    days: show calendar events for number of days (default 1)
    format: display format for this module
        (default '{format_event}|\?color=event \u2687')
    format_event: display format for events
        (default '[\?if=is_focused&color=bad X ]{format_event_start}
        [{format_event_end}] [\?color=event {event}]
        [\?if=is_multiple&color=multiple *]')
    format_event_end: display format for end date/time (default None)
    format_event_start: display format for start date/time
        (default '[\?if=is_first [\?if=is_date&color=date %a %b %-d ]]
        [\?soft ][\?if=is_time&color=time %-I:%M %p]')
    format_separator: show separator if more than one (default ', ')
    ignore: specify keys and values to ignore (default {})
    remove: specify a list of strings to remove (default [])
    url: specify url to use if no event or events (default None)

Format placeholders:
    {format_event} format for calendar events

format_event_{start, end} strftime characters:
    %?             a character. See `man strftime`.

Control format_event* placeholders:
    {is_date}      a boolean based on calendar event data
    {is_time}      a boolean based on calendar event data
    {is_first}     a boolean based on calendar event data
    {is_multiple}  a boolean based on calendar event data
    {is_focused}   a boolean based on mouse scrolling data

Format_event* placeholders:
    {index}        event index
    {calendar}     which calendars, eg Default
    {description}  event description, eg Some silly description
    {email}        creator email, eg lasers@py3status.org
    {enddate}      end date, eg 2017-09-10
    {endtime}      end time, eg 07:50
    {event}        event name, eg Breakfast at Tiffany
    {hangout}      hangout link, eg (new hangout link here)
    {link}         event link, eg (new event link here)
    {location}     event location, eg Tiffany's House
    {startdate}    start date, eg 2017-09-10
    {starttime}    start time, eg 07:00

Color options:
    color_date: a date
    color_time: a time
    color_event: an event
    color_multiple: an indicator for multiple days

Requires:
    gcalcli: command line interface for Google Calendar

Examples:
```
# add arguments
gcal {
    # We use 'gcalcli agenda --tsv --details=all'
    # See `gcalcli --help' for more information.
    # Not all of the arguments will work here.

    # Don't show events that have started
    # Don't show events that have been declined
    arguments = ['nostarted', 'nodeclined']
}

# add button - open calendar
gcal {
    button_open = 1
}

# add buttons - scroll, open calendar or event, expand, reset, refresh
gcal {
    button_open = 1
    button_next = 5
    button_previous = 4
    button_refresh = 2
    button_reset = 3
}

# add colors
gcal {
    color_date = '#f3ea5f'
    color_time = '#2bd1fc'
    color_event = '#ff48c4'
    color_multiple = '#2bd1fc'
}

# add days - two is a good number
gcal {
    days = 2
}

# add end times
gcal {
    format_event_end = '[\?if=is_time&color=time  – %-I:%M %p]'
}

# add url - Gcal will forgive you for your mistakes
gcal {
    url = 'https://calendar.google.com'
}

# show '7 PM' ...... instead of '7:00 PM'
# show '7 PM – 8 PM' instead of '7:00 PM – 8:00 PM'
gcal {
    remove = [':00']
}

# show '10' .......... instead of '10:00 AM'
# show '10 – 10:50 AM' instead of '10:00 AM – 10:50 AM'
# show '10 – 11' ..... instead of '10:00 AM – 11:00 AM'
gcal {
    remove = [':00 AM', ':00 PM']
}

# show description and location - you might like them
# show calendar and email too - you might not like them
gcal {
    format_event = '[\?if=is_focused&color=bad X ]{format_event_start}'
    format_event += '[{format_event_end}] [\?color=event {event}]'
    format_event += '[\?if=is_multiple&color=multiple *]'
    format_event += '[\?if=description&color=description [\?if=is_focused  ? {description}|?]]'
    format_event += '[\?if=location&color=location [\?if=is_focused  @ {location}|@]]'
    format_event += '[\?if=calendar&color=calendar [\?if=is_focused  C {calendar}|C]]'
    format_event += '[\?if=email&color=email [\?if=is_focused  E {email}|E]]'
    color_description = '#ffaaff'
    color_location = '#aaaaff'
    color_calendar = '#aaffaa'
    color_email = '#ffffaa'
}

# ignore - sometimes we want to ignore certain events on our calendars
gcal {
    # fnmatch: *       matches everything
    # fnmatch: ?       matches any single character
    # fnmatch: [seq]   matches any character in seq
    # fnmatch: [!seq]  matches any character not in seq
    ignore = {'email': '*weather*'}
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
from fnmatch import fnmatch
import re


STRING_NOT_INSTALLED = 'not installed'
DATE = '%Y-%m-%d'
TIME = '%H:%M'


class Py3status:
    """
    """
    # available configuration parameters
    arguments = []
    button_next = None
    button_open = None
    button_previous = None
    button_refresh = None
    button_reset = None
    cache_timeout = 3600
    days = 1
    format = '{format_event}|\?color=event \u2687'
    format_event = '[\?if=is_focused&color=bad X ]{format_event_start}' +\
        '[{format_event_end}] [\?color=event {event}]' +\
        '[\?if=is_multiple&color=multiple *]'
    format_event_end = None
    format_event_start = '[\?if=is_first [\?if=is_date&color=date %a %b %-d ]]' +\
        '[\?soft ][\?if=is_time&color=time %-I:%M %p]'
    format_separator = ', '
    ignore = {}
    remove = []
    url = None

    def post_config_hook(self):
        self.command = 'gcalcli agenda --tsv --details=all'
        if not self.py3.check_commands(self.command.split()[0]):
            raise Exception(STRING_NOT_INSTALLED)
        if self.arguments:
            self.arguments = ' '.join(['--' + x for x in self.arguments])
            self.command = '%s %s' % (self.command, self.arguments)
        if self.format_event_end is None:
            self.format_event_end = ''
        self.first_run = True
        self.command += ' %s %s'
        self.re = re.compile(r'(%s)' % '|'.join(self.remove))
        self.is_scrolling = False
        self.gcal_data = None
        self.reset_url = self.url
        self.names = [
            'startdate', 'starttime', 'enddate', 'endtime', 'link', 'hangout',
            'event', 'location', 'description', 'calendar', 'email']

    def _datetime(self, e, starttime=False, endtime=False, startdate=False, enddate=False):
        if startdate:
            return datetime.strptime(e['startdate'], DATE).date()
        elif enddate:
            return datetime.strptime(e['enddate'], DATE).date() - timedelta(days=1)
        elif starttime:
            return datetime.strptime(
                '%s %s' % (e['startdate'], e['starttime']), '%s %s' % (DATE, TIME))
        elif endtime:
            return datetime.strptime(
                '%s %s' % (e['enddate'], e['endtime']), '%s %s' % (DATE, TIME))

    def _scroll(self, direction=0):
        self.is_scrolling = True
        data = self.shared
        if direction == 0:
            self.url = self.reset_url
            for d in data:
                d['is_focused'] = False
        else:
            if data and not any(d for d in data if d['is_focused']):
                data[0]['is_focused'] = True

            length = len(data)
            for index, d in enumerate(data):
                if d.get('is_focused'):
                    data[index]['is_focused'] = False
                    if direction < 0:  # switch previous
                        if index > 0:
                            data[index - 1]['is_focused'] = True
                        else:
                            data[index]['is_focused'] = True
                    elif direction > 0:  # switch next
                        if index < (length - 1):
                            data[index + 1]['is_focused'] = True
                        else:
                            data[length - 1]['is_focused'] = True
                    break

            for d in data:
                if d['is_focused']:
                    self.url = d['link']
                    break

        self._manipulate(data)

    def _get_gcal_data(self):
        now = datetime.now()
        start = datetime.strftime(now, DATE)
        end = datetime.strftime(now + timedelta(days=self.days), DATE)
        return self.py3.command_output(self.command % (start, end))

    def _organize(self, data):
        self.url = self.reset_url

        new_data = []
        for line in data.splitlines():
            new_event = dict(zip(self.names, line.split('\t')))

            if not self.ignore:
                new_data.append(new_event)
                continue

            append_event = True
            for placeholder, data in new_event.items():
                for key, value in self.ignore.items():
                    if placeholder == key and fnmatch(data, value):
                        append_event = False
                        break

            if append_event:
                new_data.append(new_event)

        return new_data

    def _manipulate(self, data):
        self.shared = data
        first_loop = True
        last_date = None
        new_data = []

        for index, e in enumerate(data, 1):
            e['index'] = index
            e['is_date'] = True
            e['is_time'] = True
            e['is_first'] = False
            e['is_multiple'] = False
            if not self.is_scrolling:
                e['is_focused'] = False
            if self._datetime(e, startdate=True) < self._datetime(e, enddate=True):
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

            start = self._datetime(e, starttime=True)
            start = self.re.sub('', datetime.strftime(start, self.format_event_start))
            end = self._datetime(e, endtime=True)
            end = self.re.sub('', datetime.strftime(end, self.format_event_end))

            new_data.append(self.py3.safe_format(
                self.format_event, dict(
                    format_event_start=self.py3.safe_format(start, dict(**e)),
                    format_event_end=self.py3.safe_format(end, dict(**e)),
                    **e)))

        return new_data

    def gcal(self):
        cached_until = self.cache_timeout
        format_event = None
        data = self.gcal_data

        if self.first_run:
            self.first_run = False
            cached_until = 0
        else:
            if not self.is_scrolling:
                data = self.gcal_data = self._organize(self._get_gcal_data())
            data = self._manipulate(data)
            format_separator = self.py3.safe_format(self.format_separator)
            format_event = self.py3.composite_join(format_separator, data)

        self.is_scrolling = False
        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(
                self.format, {'format_event': format_event})
        }

    def on_click(self, event):
        button = event['button']
        if button == self.button_next and self.gcal_data:
            self._scroll(+1)
        elif button == self.button_previous and self.gcal_data:
            self._scroll(-1)
        elif button == self.button_reset and self.gcal_data:
            self._scroll(0)
        elif button == self.button_open and self.url:
            self.py3.command_run('xdg-open %s' % self.url)
            if self.gcal_data:
                self._scroll(0)
            else:
                self.py3.prevent_refresh()
        elif button != self.button_refresh:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
