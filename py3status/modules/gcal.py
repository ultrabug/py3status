# -*- coding: utf-8 -*-
"""
Display upcoming calendar events from Google Calendar.

Configuration parameters:
    agenda_days: show calendar events for number of days (default 1)
    button_refresh: mouse button to refresh this module (default 2)
    cache_timeout: refresh interval for this module (default 21600)
    format: display format for this module (default '{format_event}')
    format_event: display format for events
        (default '[\?if=is_date&color=degraded %a %b %d ]
        [\?if=is_time&color=good %-I:%M %p ][\?color=bad {event}]')
    format_separator: show separator only if more than one (default ', ')
    remove: list of strings to be removed from the output (default [])

Format placeholders:
    {format_event} format for events
    is_event: a boolean based on available events

format_event placeholders:
    {event} scheduled event eg Pizza night
    %?  strftime characters to be translated. See `man strftime'.
    is_time: a boolean based on event containing a time schedule
    is_date: a boolean based on event containing a date schedule

Requires:
    gcalcli: Google Calendar Command Line Interface

Examples:
```
# change event colors
gcal {
    color_bad = '#ad7fa8'
    color_degraded = '#fce94f'
    color_good = '#34e2e2'
}
# show "No Events"
gcal {
    format = u'[\?if=is_event {format_event}|\?color=bad No Events]'
}
```

@author lasers

SAMPLE OUTPUT
[
    {'color': '#FFFF00', 'full_text': u'Fri Jul 20 '},
    {'color': '#FF0000', 'full_text': u'Tacos'},
    {'full_text': u', '},
    {'color': '#FF0000', 'full_text': u'Volleyball'},
    {'full_text': u', '},
    {'color': '#00FF00', 'full_text': u'6:00 AM '},
    {'color': '#FF0000', 'full_text': u'Garbage Pickup'},
    {'full_text': u', '}
    {'color': '#FFFF00', 'full_text': u'Sat Jul 21 '},
    {'color': '#00FF00', 'full_text': u'6:05 PM '},
    {'color': '#FF0000', 'full_text': u'Flight to Poland'}
]
"""

from datetime import datetime as dt, timedelta
import re

STRING_NOT_INSTALLED = "isn't installed"
FMT_DATE = '%a %b %d'
FMT_GCAL = '%Y%m%d'
FMT_SS = '%s %s'
FMT_TIME = '%I:%M%p'


class Py3status:
    """
    """
    # available configuration parameters
    agenda_days = 1
    button_refresh = 2
    cache_timeout = 21600
    format = u'{format_event}'
    format_event = '[\?if=is_date&color=degraded %a %b %d ]' +\
                   '[\?if=is_time&color=good %-I:%M %p ]' +\
                   '[\?color=bad {event}]'
    format_separator = ', '
    remove = []

    def post_config_hook(self):
        self.cmd = 'gcalcli agenda --nocolor %s %s'
        if not self.py3.check_commands(self.cmd.split(' ', 1)[0]):
            raise Exception(STRING_NOT_INSTALLED)

        remove = '|'.join(self.remove)
        self.re = re.compile(r'(' + remove + ')')

    def _get_gcal_data(self):
        now = dt.now()
        start = dt.strftime(now, FMT_GCAL)
        end = dt.strftime(now + timedelta(days=self.agenda_days), FMT_GCAL)
        return self.py3.command_output(self.cmd % (start, end))

    def _organize_data(self, data):
        new_data, is_event = [], True
        for out in data.splitlines():
            temporary = {}
            if 'No Events Found' in out:
                is_event = False
                break
            if out.rstrip():
                temporary['date'] = out[:10].strip()
                temporary['time'] = out[10:20].strip()
                temporary['event'] = out[20:].strip()
                temporary = {k: v for k, v in temporary.items() if v}
                new_data.append(temporary)

        return is_event, new_data

    def _manipulate_data(self, data):
        new_data = []
        for e in data:
            obj, is_date, is_time = None, False, False
            if 'date' in e:
                is_date = True
                if 'time' in e:
                    is_time = True
                    obj = dt.strptime(FMT_SS % (
                        e['date'], e['time']), FMT_SS % (FMT_DATE, FMT_TIME))
                else:
                    obj = dt.strptime(e['date'], FMT_DATE)
            elif 'time' in e:
                is_time = True
                obj = dt.strptime(e['time'], FMT_TIME)
            if obj:
                _fmt = self.re.sub('', dt.strftime(obj, self.format_event))

            new_data.append(self.py3.safe_format(_fmt,
                                                 dict(
                                                     event=e.get('event'),
                                                     is_date=is_date,
                                                     is_time=is_time)))
        return new_data

    def gcal(self):
        """
        """
        data = self._get_gcal_data()
        is_event, data = self._organize_data(data)
        data = self._manipulate_data(data)

        format_separator = self.py3.safe_format(self.format_separator)
        format_event = self.py3.composite_join(format_separator, data)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format,
                                              dict(
                                                  format_event=format_event,
                                                  is_event=is_event,
                                              ))
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
