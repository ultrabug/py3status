# -*- coding: utf-8 -*-
"""
Display upcoming Google Calendar events.

This module will display information about upcoming Google Calendar events in
one of two formats which can be toggled with a button press. The
event's URL may also be opened in a web browser with a button press.

Configuration parameters:
    auth_token: The path to where the access/refresh token will be saved
        after successful credential authorization.
        (default '~/.config/py3status/google_calendar.auth_token')
    button_open: Opens the URL for the clicked on event in the default
        web browser.
        (default 3)
    button_refresh: Refreshes the module and updates the list of events.
        (default 2)
    button_toggle: The button used to toggle between output formats
        format_event and format_event_full.
        (default 1)
    cache_timeout: How often the module is refreshed in seconds
        (default 60)
    client_secret: the path to your client_secret file which
        contains your OAuth 2.0 credentials.
        (default '~/.config/py3status/google_calendar.client_secret')
    format: The format for module output.
        (default '{events}|')
    format_date: The format for date related format placeholders. May be any Python
        strftime directives for dates.
        (default '%a %d-%m')
    format_event: The format for the first toggleable event output.
        (default '\?color=event {summary} {time_to}')
    format_event_full: The format for the second toggleable event output.
        (default '[\?color=event {summary}]
        [\?color=time ({start_time} - {end_time}, {start_date})]')
    format_separator: The string used to separate individual events.
        (default '\?color=separator \| ')
    format_time: The format for time related format placeholders (except {time_to}).
        May use any Python strftime directives for times.
        (default '%I:%M %p')
    format_time_left: The format for used for the {time_to} placeholder when when the time
        displayed is the time left until an event in progress is over.
        (default '\?color=time ({days}d {hours}h {minutes}m) left')
    format_time_to: The format used for the {time_to} placeholder.
        (default '\?color=time ({days}d {hours}h {minutes}m)')
    num_events: The maximum number of events to display.
        (default 3)
    thresholds: Thresholds for events. The first entry is the color for event 1,
        the second for event 2, and so on.
        (default [])
    time_to_max: Threshold (in minutes) for when to display the {time_to}
        string; e.g. if time_to_max = 60, {time_to} will only be displayed
        for events starting in 60 minutes or less.
        (default 180)
    warn_threshold: The number of minutes until an event starts before a warning is
        displayed to notify the user; e.g. if warn_threshold = 30 and an event is
        starting in 30 minutes or less, a notification will be displayed. disabled (= 0)
        by default.
        (default 0)
    warn_timeout: The number of seconds before a warning should be displayed again.
        (default 300)

Format placeholders:
    {events} All the events to display.

Format_error placeholders:
    {error} Error to display.

Format_event & format_event_full placeholders:
    {description} The description for the calendar event.
    {end_date} The end date for the event.
    {end_time} The end time for the event.
    {location} The location for the event.
    {start_date} The start date for the event.
    {start_time} The start time for the event.
    {summary} The summary (i.e. title) for the event.
    {time_to} The time until the event starts (or until it is over
        if already in progress).

Format_time_to and format_time_left placeholders:
    {days} The number of days until the event.
    {hours} The number of hours until the event.
    {minutes} The number of minutes until the event.

Color options:
    color_separator: Color for separator.
    color_event: Color for a single event.
    color_time: Color for the time associated with each event.

Requires:
    1. Python library google-api-python-client (can be obtained with pip).
    2. OAuth 2.0 credentials for the Google Calendar api.

    Follow Step 1 of the guide here to obtain your OAuth 2.0 credentials:
    https://developers.google.com/google-apps/calendar/quickstart/python

    Download the client_secret.json file which contains your client ID and
    client secret. In your i3status config file, set configuration parameter
    client_secret to the path to your client_secret.json file.

    The first time you run the module, a browser window will open asking you
    to authorize access to your calendar. After authorization is complete,
    an access/refresh token will be saved to the path configured in
    auth_token, and i3status will be restarted. This restart will
    occur only once after the first time you successfully authorize.

Examples:
```
# add color gradients for events and dates/times
google_calendar {
    thresholds = {
        'event': [(1, '#d0e6ff'), (2, '#bbdaff'), (3, '#99c7ff'), (4, '#86bcff'),
            (5, '#62a9ff'), (6, '#8c8cff'), (7, '#7979ff')],
        'time': [(1, '#ffcece'), (2, '#ffbfbf'), (3, '#ff9f9f'), (4, '#ff7f7f'),
            (5, '#ff5f5f'), (6, '#ff3f3f'), (7, '#ff1f1f')]
    }
}
```

@author Igor Grebenkov
@license BSD
"""

import httplib2
import os
import datetime

from apiclient import discovery
from oauth2client import client
from oauth2client import clientsecrets
from oauth2client import tools
from oauth2client.file import Storage
from httplib2 import ServerNotFoundError


SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
APPLICATION_NAME = 'py3status google_calendar module'


class Py3status:
    auth_token = '~/.config/py3status/google_calendar.auth_token'
    button_open = 3
    button_refresh = 2
    button_toggle = 1
    cache_timeout = 60
    client_secret = '~/.config/py3status/google_calendar.client_secret'
    format = '{events}|'
    format_date = '%a %d-%m'
    format_event = '\?color=event {summary} {time_to}'
    format_event_full = '[\?color=event {summary}] ' +\
        '[\?color=time ({start_time} - {end_time}, {start_date})]'
    format_separator = '\?color=separator \| '
    format_time = '%I:%M %p'
    format_time_left = '\?color=time ({days}d {hours}h {minutes}m) left'
    format_time_to = '\?color=time ({days}d {hours}h {minutes}m)'
    num_events = 3
    thresholds = []
    time_to_max = 180
    warn_threshold = 0
    warn_timeout = 300

    def post_config_hook(self):
        self.button = None
        self.button_states = [False] * self.num_events
        self.events = None
        self.no_update = False

        self.client_secret = os.path.expanduser(self.client_secret)
        self.auth_token = os.path.expanduser(self.auth_token)

        self.credentials = self._get_credentials()
        self.is_authorized = self._authorize_credentials()

    def _get_credentials(self):
        """
        Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns: Credentials, the obtained credential.
        """
        client_secret_path = os.path.dirname(self.client_secret)
        auth_token_path = os.path.dirname(self.auth_token)

        if not os.path.exists(auth_token_path):
            os.makedirs(auth_token_path)

        if not os.path.exists(client_secret_path):
            os.makedirs(client_secret_path)

        flags = tools.argparser.parse_args(args=[])
        store = Storage(self.auth_token)
        credentials = store.get()

        if not credentials or credentials.invalid:
            try:
                flow = client.flow_from_clientsecrets(self.client_secret, SCOPES)
                flow.user_agent = APPLICATION_NAME
                if flags:
                    credentials = tools.run_flow(flow, store, flags)
                else:  # Needed only for compatibility with Python 2.6
                    credentials = tools.run(flow, store)
            except clientsecrets.InvalidClientSecretsError:
                raise Exception('missing client_secret')

            """
            Have to restart i3 after getting credentials to prevent bad output.
            This only has to be done once on the first run of the module.
            """
            self.py3.command_output('i3-msg restart')

        return credentials

    def _authorize_credentials(self):
        """
        Fetches an access/refresh token by authorizing OAuth 2.0 credentials.

        Returns: True, if the authorization was successful.
                 False, if a ServerNotFoundError is thrown.
        """
        try:
            http = self.credentials.authorize(httplib2.Http())
            self.service = discovery.build('calendar', 'v3', http=http)
            return True
        except ServerNotFoundError:
            return False

    def _get_events(self):
        """
        Fetches events from the color into a list.

        Returns: The list of events.
        """
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

        eventsResult = self.service.events().list(
            calendarId='primary', timeMin=now, maxResults=self.num_events, singleEvents=True,
            orderBy='startTime').execute()
        return eventsResult.get('items', [])

    def _check_warn_threshold(self, time_to, summary):
        """
        Checks if the time until an event starts is less than or equal to the warn_threshold.
        If it is, it presents a warning with self.py3.notify_user.
        """
        if time_to['total_minutes'] <= self.warn_threshold:
            self.py3.notify_user("Warning: Appointment " + str(summary) +
                                 " coming up!", 'warning', self.warn_timeout)

    def _gstr_to_date(self, date_str):
        """ Returns a dateime object from a google calendar date string."""
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')

    def _gstr_to_datetime(self, date_time_str):
        """ Returns a datetime object from a google calendar date/time string."""
        tmp = '-'.join(date_time_str.split('-')[:-1])
        return datetime.datetime.strptime(tmp, '%Y-%m-%dT%H:%M:%S')

    def _datetime_to_str(self, date_time, dt_format):
        """ Returns a strftime formatted string from a datetime object."""
        return date_time.strftime(dt_format)

    def _delta_time(self, date_time):
        """
        Returns in a dict the number of days/hours/minutes and total minutes
        until date_time.
        """
        now = datetime.datetime.now()
        diff = date_time - now

        days = int(diff.days)
        hours = int(diff.seconds / 3600)
        minutes = int((diff.seconds / 60) - (hours * 60)) + 1
        total_minutes = int((diff.seconds / 60) + (days * 24 * 60)) + 1

        return {'days': days,
                'hours': hours,
                'minutes': minutes,
                'total_minutes': total_minutes}

    def _format_timedelta(self, index, time_delta, format):
        """
        Formats the dict time_to containg days/hours/minutes until an event starts
        into a string according to time_to_formatted.

        Returns: The formatted string.
        """
        time_delta_formatted = ''

        if time_delta['total_minutes'] <= self.time_to_max:
            time_delta_formatted = self.py3.safe_format(
                format,
                {'days': time_delta['days'],
                 'hours': time_delta['hours'],
                 'minutes': time_delta['minutes']})

        return time_delta_formatted

    def _check_button_open(self, index, url):
        """
        Checks if the button associated with opening an event's URL in a browser has
        been pressed. If so, that URL is opened in the default web browser.
        """
        if self.button == self.button_open and self.button_index == index:
            self.py3.command_run('xdg-open ' + url)

            self.no_update = False
            self.button = None

    def _check_button_toggle(self, index):
        """
        Checks if the button associated with toggling event format between
        format_event and format_event_full has been pressed. If so,
        we toggle the format.
        """
        if self.button == self.button_toggle and self.button_states[index]:
            curr_event_format = self.format_event_full
        else:
            curr_event_format = self.format_event

        self.no_update = False

        return curr_event_format

    def _build_response(self):
        """
        Builds the composite reponse to be output by the module by looping through all
        events and formatting the necessary strings.

        Returns: A composite containing the individual response for each event.
        """
        responses = []
        index = 0

        self.last_update = datetime.datetime.now()

        for event in self.events:
            self.py3.threshold_get_color(index + 1, 'event')
            self.py3.threshold_get_color(index + 1, 'time')

            summary = event.get('summary')
            location = event.get('location')
            description = event.get('description')
            url = event['htmlLink']

            if event['start'].get('date') is not None:
                start_dt = self._gstr_to_date(event['start'].get('date'))
                end_dt = self._gstr_to_date(event['end'].get('date'))
            else:
                start_dt = self._gstr_to_datetime(event['start'].get('dateTime'))
                end_dt = self._gstr_to_datetime(event['end'].get('dateTime'))

            start_time_str = self._datetime_to_str(start_dt, self.format_time)
            end_time_str = self._datetime_to_str(end_dt, self.format_time)

            start_date_str = self._datetime_to_str(start_dt, self.format_date)
            end_date_str = self._datetime_to_str(end_dt, self.format_date)

            time_delta = self._delta_time(start_dt)

            if time_delta['days'] < 0:
                time_delta = self._delta_time(end_dt)
                time_delta_formatted = self._format_timedelta(index, time_delta,
                                                              self.format_time_left)
            else:
                time_delta_formatted = self._format_timedelta(index, time_delta,
                                                              self.format_time_to)
            self._check_warn_threshold(time_delta, summary)
            self._check_button_open(index, url)

            curr_event_format = self._check_button_toggle(index)

            event_formatted = self.py3.safe_format(
                curr_event_format,
                {'summary': summary,
                 'location': location,
                 'description': description,
                 'start_time': start_time_str,
                 'end_time': end_time_str,
                 'start_date': start_date_str,
                 'end_date': end_date_str,
                 'time_to': time_delta_formatted})

            self.py3.composite_update(event_formatted, {'index': index})
            responses.append(event_formatted)

            index += 1

        format_separator = self.py3.safe_format(self.format_separator)
        responses = self.py3.composite_join(format_separator, responses)

        return {'events': responses}

    def google_calendar(self):
        """
        The method that outputs the response.

        First, we check credential authorization. If no authorization, we display an error message,
        and try authorizing again in 5 seconds.

        Otherwise, we fetch the events, build the response, and output the resulting composite.
        """
        if not self.is_authorized:
            self.is_authorized = self._authorize_credentials()

            return {'cached_until': self.py3.time_in(self.cache_timeout),
                    'full_text': self.py3.safe_format(self.format)}
        else:
            if not self.no_update:
                self.events = self._get_events()

            return {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'composite': self.py3.safe_format(self.format, self._build_response())
            }

    def on_click(self, event):
        if self.is_authorized and self.events is not None:
            """
            If button_refresh is clicked, we allow the events to be updated if the
            last event update occured at least 1 second ago. This prevents a bug that
            can crash py3status since refreshing the module too fast results in
            incomplete event information being fetched as _get_events() is called
            repeatedly.

            Otherwise, we disable event updates.
            """
            try:
                self.no_update = True

                self.button = event['button']
                self.button_index = event['index']

                if self.button == self.button_toggle:
                    self.button_states[self.button_index] = \
                        not self.button_states[self.button_index]
                elif self.button == self.button_refresh:
                    now = datetime.datetime.now()
                    diff = (now - self.last_update).seconds
                    if diff > 1:
                        self.no_update = False

            except IndexError:
                return


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
