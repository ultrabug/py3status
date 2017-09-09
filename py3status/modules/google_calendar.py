# -*- coding: utf-8 -*-
"""
Display upcoming Google Calendar events.

This module will display information about upcoming Google Calendar events in
either compact or full format which can be toggled with a button press. The
events URL may also be opened in a web browser with a button press.

Configuration parameters:
    auth_token_path = The path to where the access/refresh token will be saved
        after successful credential authorization.
        (default '~/.credentials')
    button_toggle_format: The button used to toggle between output formats
        format_event_full and format_event_compact.
        (default 1)
    button_open_url: Opens the URL for the clicked on event in the default
        web browser.
        (default 3)
    cache_timeout: How often the module is refreshed in seconds
        (default 60)
    client_secret_path: the path to your client_secret.json file which
        contains your OAuth 2.0 credentials.
        (default '')
    colors: A list of color strings specifying what color to display events
        the first color in the list will be used for the next upcoming
        event, the second color for the event after that, and so on; if
        the number of colors is less than the number of events displayed,
        the rest of the list will be padded with '#FFFFFF' (white).
        (default [])
    event_in_progress_suffix:  The suffix used to indicate that the {time_until}
        format placeholder is referring to the time until an event in progress is
        over; e.g. if an event is 10 mins past its start time and there are 50 minutes
        left until it is over, '{time_until} event_in_progress_suffix' will be displayed.
        (default 'Remaining')
    format: The format for module output.
        (default '{events}')
    format_date: The format for date related format placeholders. May be any Python
        strftime directives for dates.
        (default '%a %d-%m')
    format_error: The format used for error related output.
        (default '')
    format_event_compact: The format for individual event output, intended
        to be used for more compact output with less data displayed.
        (default '{summary} {time_until}')
    format_event_full: The format for individual event output, intended to
        be used for extended event information with more data displayed.
        (default '{summary} ({start_time} - {end_time}), {start_date})')
    format_time: The format for time related format placeholders (except {time_until}).
        May use any Python strftime directives for times.
        (default '%I:%M %p')
    format_time_until: The format used for the {time_until} placeholder.
        (default '({days}d {hours}h {mins}m)')
    num_events: The maximum number of events to display.
        (default 3)
    separator: The string used to separate individual events.
        (default '|')
    time_until_threshold: Threshold (in minutes) for when to display the {time_until}
        string; e.g. if time_until_threshold = 60, {time_until} will only be displayed
        for events starting in 60 minutes or less.
        (default 180)
    warn_threshold: The number of minutes until an event starts before a warning is
        displayed to notify the user; e.g. if warn_threshold = 30 and an event is
        starting in 30 mins or less, a notification will be displayed. disabled (= 0)
        by default.
        (default 0)
    warn_timeout: The number of seconds before a warning should be displayed again.
        (default 300)

format placeholders:
    {events} All the events to display.

format_error placeholders:
    {error} Error to display.

format_event_full & format_event_compact placeholders:
    {description} The description for the calendar event.
    {end_date} The end date for the event.
    {end_time} The end time for the event.
    {location} The location for the event.
    {start_date} The start date for the event.
    {start_time} The start time for the event.
    {summary} The summary (i.e. title) for the event.
    {time_until} The time until the event starts.

format_time_until placeholders:
    {days} The number of days until the event.
    {hours} The number of hours until the event.
    {mins} The number of minutes until the event.

Requires:
    1. Python library google-api-python-client (can be obtained with pip).
    2. OAuth 2.0 credentials for the Google Calendar api.

    Follow Step 1 of the guide here to obtain your OAuth 2.0 credentials:
    https://developers.google.com/google-apps/calendar/quickstart/python

    Download the client_secret.json file which contains your client ID and
    client secret. In your i3status config file, set configuration parameter
    client_secret_path to the path to your client_secret.json file.

    The first time you run the module, a browser window will open asking you
    to authorize access to your calendar. After authorization is complete,
    an access/refresh token will be saved to the path configured in
    auth_token_path, and i3status will be restarted. This restart will
    occur only once after the first time you successfully authorize.

Example:
```
google_calendar {
    client_secret_path = '/path/to/client_secret/'
    auth_token_path = '/path/to/auth_token/'
}
```
@author Igor Grebenkov
@license BSD
"""

import httplib2
import os
import datetime
import webbrowser

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from httplib2 import ServerNotFoundError


SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
APPLICATION_NAME = 'py3status google_calendar module'


def gstr_to_datetime(date_time_str):
    """ Returns a datetime object from a google calendar date/time string."""
    tmp = '-'.join(date_time_str.split('-')[:-1])
    return datetime.datetime.strptime(tmp, '%Y-%m-%dT%H:%M:%S')


def datetime_to_str(date_time, dt_format):
    """ Returns a strftime formatted string from a datetime object."""
    return date_time.strftime(dt_format)


def delta_time(date_time):
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


class Py3status:
    auth_token_path = '~/.credentials'
    button_toggle_format = 1
    button_open_url = 3
    cache_timeout = 60
    client_secret_path = ''
    colors = []
    event_in_progress_suffix = 'Remaining'
    format = '{events}'
    format_date = '%a %d-%m'
    format_error = ''
    format_event_compact = '{summary} {time_until}'
    format_event_full = '{summary} ({start_time} - {end_time}, {start_date})'
    format_time = '%I:%M %p'
    format_time_until = '({days}d {hours}h {mins}m)'
    num_events = 3
    separator = '|'
    time_until_threshold = 180
    warn_threshold = 0
    warn_timeout = 300

    def post_config_hook(self):
        self.button = None
        self.button_states = [False] * self.num_events
        self.events = None
        self.no_update = False
        self.colors.extend(['#FFFFFF'] * (self.num_events - len(self.colors)))

        self.credentials = self._get_credentials()
        self.is_authorized = self._authorize_credentials()

    def _get_credentials(self):
        """
        Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns: Credentials, the obtained credential.
        """
        CLIENT_SECRET_FILE = os.path.join(os.path.expanduser(self.client_secret_path),
                                          'client_secret.json')

        if not os.path.exists(os.path.expanduser(self.auth_token_path)):
            os.makedirs(os.path.expanduser(self.auth_token_path))

        self.auth_token_path = os.path.join(os.path.expanduser(self.auth_token_path),
                                            'py3status-gcal.json')

        flags = tools.argparser.parse_args(args=[])
        store = Storage(self.auth_token_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)

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

    def _check_warn_threshold(self, time_until, summary):
        """
        Checks if the time until an event starts is less than or equal to the warn_threshold.
        If it is, it presents a warning with self.py3.notify_user.
        """
        if time_until['total_minutes'] <= self.warn_threshold:
            self.py3.notify_user("Warning: Appointment " + str(summary) +
                                 " coming up!", 'warning', self.warn_timeout)

    def _format_timedelta(self, index, time_until):
        """
        Formats the dict time_until containg days/hours/minutes until an event starts
        into a string according to time_until_formatted.

        Returns: The formatted string.
        """
        time_until_formatted = ''

        if time_until['total_minutes'] <= self.time_until_threshold:
            time_until_formatted = self.py3.safe_format(
                self.format_time_until,
                {'days': time_until['days'],
                 'hours': time_until['hours'],
                 'mins': time_until['minutes']})

        return time_until_formatted

    def _check_button_open_url(self, index, url):
        """
        Checks if the button associated with opening an event's URL in a browser has
        been pressed. If so, that URL is opened in the default web browser.

        Note: stdout is temporarily redirected to /dev/null before the link is opened
              to prevent messing up py3status output since opening the browser normally
              prints a string to stdout indicating the browser has been opened.
        """
        if self.button == self.button_open_url and self.button_index == index:
            # We have to temporarily redirect stdout to prevent messing up output
            save_out = os.dup(1)
            os.close(1)

            os.open(os.devnull, os.O_RDWR)
            try:
                webbrowser.open(url)
            finally:
                os.dup2(save_out, 1)

            self.no_update = False
            self.button = None

    def _check_button_toggle_format(self, index):
        """
        Checks if the button associated with toggling event format between
        format_event_full and format_event_compact has been pressed. If so,
        we toggle the format.
        """
        if self.button == self.button_toggle_format and self.button_states[index]:
            curr_event_format = self.format_event_full
        else:
            curr_event_format = self.format_event_compact

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

        for event in self.events:
            summary = event.get('summary')
            location = event.get('location')
            description = event.get('description')
            url = event['htmlLink']

            start_dt = gstr_to_datetime(event['start'].get('dateTime'))
            end_dt = gstr_to_datetime(event['end'].get('dateTime'))

            start_time_str = datetime_to_str(start_dt, self.format_time)
            end_time_str = datetime_to_str(end_dt, self.format_time)

            start_date_str = datetime_to_str(start_dt, self.format_date)
            end_date_str = datetime_to_str(end_dt, self.format_date)

            time_until = delta_time(start_dt)

            self._check_warn_threshold(time_until, summary)

            if time_until['days'] < 0:
                time_until = delta_time(end_dt)
                time_until_formatted = '{} {}'.format(self._format_timedelta(index, time_until),
                                                      self.event_in_progress_suffix)
            else:
                time_until_formatted = self._format_timedelta(index, time_until)

            self._check_button_open_url(index, url)

            curr_event_format = self._check_button_toggle_format(index)

            event_formatted = self.py3.safe_format(
                curr_event_format,
                {'summary': summary,
                 'location': location,
                 'description': description,
                 'start_time': start_time_str,
                 'end_time': end_time_str,
                 'start_date': start_date_str,
                 'end_date': end_date_str,
                 'time_until': time_until_formatted})

            responses.append({
                'full_text': event_formatted,
                'color': self.colors[index], 'index': index})

            if index < self.num_events - 1:
                responses.append({'full_text': ' {} '.format(self.separator), 'index': 'sep'})

            index += 1

        return {'events': self.py3.composite_create(responses)}

    def google_calendar(self):
        """
        The method that outputs the response.

        First, we check credential authorization. If no authorization, we display an error message,
        and try authorizing again in 5 seconds.

        Otherwise, we fetch the events, build the response, and output the resulting composite.
        """
        if not self.is_authorized:
            self.is_authorized = self._authorize_credentials()

            error_msg = self.py3.safe_format(
                self.format_error,
                {'error':
                 'ServerNotFoundError: Check your internet connection!'})

            return {'cached_until': self.py3.time_in(5),
                    'full_text': error_msg,
                    'color': '#FF0000'}
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
            If a button is clicked, we stop updating self.events until the
            button event is handled. This prevents errors when the on_click()
            method is called during an event update (using _get_events()), which
            can cause a crash in the module and/or py3status.
            """
            self.no_update = True

            self.button = event['button']
            self.button_index = event['index']
            if self.button == self.button_toggle_format and self.button_index != 'sep':
                self.button_states[self.button_index] = not self.button_states[self.button_index]


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
