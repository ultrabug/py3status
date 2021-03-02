"""
Display upcoming Google Calendar events.

This module will display information about upcoming Google Calendar events
in one of two formats which can be toggled with a button press. The event
URL may also be opened in a web browser with a button press.

Some events details can be retreived in the Google Calendar API Documentation.
https://developers.google.com/calendar/v3/reference/events

Configuration parameters:
    auth_token: The path to where the access/refresh token will be saved
        after successful credential authorization.
        (default '~/.config/py3status/google_calendar.auth_token')
    blacklist_events: Event names in this list will not be shown in the module
        (case insensitive).
        (default [])
    browser_invocation: Command to run to open browser. Curly braces stands for URL opened.
        (default "xdg-open {}")
    button_open: Opens the event URL in the default web browser.
        (default 3)
    button_refresh: Refreshes the module and updates the list of events.
        (default 2)
    button_toggle: Toggles a boolean to hide/show the data for each event.
        (default 1)
    cache_timeout: How often the module is refreshed in seconds
        (default 60)
    client_secret: the path to your client_secret file which
        contains your OAuth 2.0 credentials.
        (default '~/.config/py3status/google_calendar.client_secret')
    events_within_hours: Select events within the next given hours.
        (default 12)
    force_lowercase: Sets whether to force all event output to lower case.
        (default False)
    format: The format for module output.
        (default '{events}|\\?color=event \u2687')
    format_date: The format for date related format placeholders.
        May be any Python strftime directives for dates.
        (default '%a %d-%m')
    format_event: The format for each event. The information can be toggled
        with 'button_toggle' based on the value of 'is_toggled'.
        *(default '[\\?color=event {summary}][\\?if=is_toggled  ({start_time}'
        ' - {end_time}, {start_date})|[ ({location})][ {format_timer}]]')*
    format_notification: The format for event warning notifications.
        (default '{summary} {start_time} - {end_time}')
    format_separator: The string used to separate individual events.
        (default ' \\| ')
    format_time: The format for time-related placeholders except `{format_timer}`.
        May use any Python strftime directives for times.
        (default '%I:%M %p')
    format_timer: The format used for the {format_timer} placeholder to display
        time until an event starts or time until an event in progress is over.
        *(default '\\?color=time ([\\?if=days {days}d ][\\?if=hours {hours}h ]'
        '[\\?if=minutes {minutes}m])[\\?if=is_current  left]')*
    ignore_all_day_events: Sets whether to display all day events or not.
        (default False)
    num_events: The maximum number of events to display.
        (default 3)
    preferred_event_link: link to open in the browser.
        accepted values :
        hangoutLink (open the VC room associated with the event),
        htmlLink (open the event's details in Google Calendar)
        fallback to htmlLink if the preferred_event_link does not exist it the event.
        (default "htmlLink")
    response: Only display events for which the response status is
        on the list.
        Available values in the Google Calendar API's documentation,
        look for the attendees[].responseStatus.
        (default ['accepted'])
    thresholds: Thresholds for events. The first entry is the color for event 1,
        the second for event 2, and so on.
        (default [])
    time_to_max: Threshold (in minutes) for when to display the `{format_timer}`
        string; e.g. if time_to_max is 60, `{format_timer}` will only be
        displayed for events starting in 60 minutes or less.
        (default 180)
    warn_threshold: The number of minutes until an event starts before a
        warning is displayed to notify the user; e.g. if warn_threshold is 30
        and an event is starting in 30 minutes or less, a notification will be
        displayed. disabled by default.
        (default 0)
    warn_timeout: The number of seconds before a warning should be issued again.
        (default 300)


Control placeholders:
    {is_toggled} a boolean toggled by button_toggle

Format placeholders:
    {events} All the events to display.

format_event and format_notification placeholders:
    {description} The description for the calendar event.
    {end_date} The end date for the event.
    {end_time} The end time for the event.
    {location} The location for the event.
    {start_date} The start date for the event.
    {start_time} The start time for the event.
    {summary} The summary (i.e. title) for the event.
    {format_timer} The time until the event starts (or until it is over
        if already in progress).

format_timer placeholders:
    {days} The number of days until the event.
    {hours} The number of hours until the event.
    {minutes} The number of minutes until the event.

Color options:
    color_event: Color for a single event.
    color_time: Color for the time associated with each event.

Requires:
    1. Python library google-api-python-client.
    2. Python library python-dateutil.
    3. OAuth 2.0 credentials for the Google Calendar api.

    Follow Step 1 of the guide here to obtain your OAuth 2.0 credentials:
    https://developers.google.com/google-apps/calendar/quickstart/python

    Download the client_secret.json file which contains your client ID and
    client secret. In your config file, set configuration parameter
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
        'event': [(1, '#d0e6ff'), (2, '#bbdaff'), (3, '#99c7ff'),
            (4, '#86bcff'), (5, '#62a9ff'), (6, '#8c8cff'), (7, '#7979ff')],
        'time': [(1, '#ffcece'), (2, '#ffbfbf'), (3, '#ff9f9f'),
            (4, '#ff7f7f'), (5, '#ff5f5f'), (6, '#ff3f3f'), (7, '#ff1f1f')]
    }
}
```

@author Igor Grebenkov
@license BSD

SAMPLE OUTPUT
[
   {'full_text': "Homer's Birthday (742 Evergreen Terrace) (1h 23m) | "},
   {'full_text': "Doctor's Appointment | Lunch with John"},
]
"""

import httplib2
import datetime
import time
from pathlib import Path

try:
    from googleapiclient import discovery
except ImportError:
    from apiclient import discovery
from oauth2client import client
from oauth2client import clientsecrets
from oauth2client import tools
from oauth2client.file import Storage
from httplib2 import ServerNotFoundError
from dateutil import parser
from dateutil.tz import tzlocal

SCOPES = "https://www.googleapis.com/auth/calendar.readonly"
APPLICATION_NAME = "py3status google_calendar module"


class Py3status:
    """
    """

    # available configuration parameters
    auth_token = "~/.config/py3status/google_calendar.auth_token"
    blacklist_events = []
    browser_invocation = "xdg-open {}"
    button_open = 3
    button_refresh = 2
    button_toggle = 1
    cache_timeout = 60
    client_secret = "~/.config/py3status/google_calendar.client_secret"
    events_within_hours = 12
    force_lowercase = False
    format = "{events}|\\?color=event \u2687"
    format_date = "%a %d-%m"
    format_event = (
        r"[\?color=event {summary}][\?if=is_toggled  ({start_time}"
        " - {end_time}, {start_date})|[ ({location})][ {format_timer}]]"
    )
    format_notification = "{summary} {start_time} - {end_time}"
    format_separator = r" \| "
    format_time = "%I:%M %p"
    format_timer = (
        r"\?color=time ([\?if=days {days}d ][\?if=hours {hours}h ]"
        r"[\?if=minutes {minutes}m])[\?if=is_current  left]"
    )
    ignore_all_day_events = False
    num_events = 3
    preferred_event_link = "htmlLink"
    response = ["accepted"]
    thresholds = []
    time_to_max = 180
    warn_threshold = 0
    warn_timeout = 300

    def post_config_hook(self):
        self.button_states = [False] * self.num_events
        self.events = None
        self.no_update = False

        self.client_secret = Path(self.client_secret).expanduser()
        self.auth_token = Path(self.auth_token).expanduser()

        self.credentials = self._get_credentials()
        self.is_authorized = False

    def _get_credentials(self):
        """
        Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns: Credentials, the obtained credential.
        """
        client_secret_path = self.client_secret.parent
        auth_token_path = self.auth_token.parent

        auth_token_path.mkdir(parents=True, exist_ok=True)
        client_secret_path.mkdir(parents=True, exist_ok=True)

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
                raise Exception("missing client_secret")
            """
            Have to restart i3 after getting credentials to prevent bad output.
            This only has to be done once on the first run of the module.
            """
            self.py3.command_run(f"{self.py3.get_wm_msg()} restart")

        return credentials

    def _authorize_credentials(self):
        """
        Fetches an access/refresh token by authorizing OAuth 2.0 credentials.

        Returns: True, if the authorization was successful.
                 False, if a ServerNotFoundError is thrown.
        """
        try:
            http = self.credentials.authorize(httplib2.Http())
            self.service = discovery.build("calendar", "v3", http=http)
            return True
        except ServerNotFoundError:
            return False

    def _get_events(self):
        """
        Fetches events from the calendar into a list.

        Returns: The list of events.
        """
        self.last_update = time.perf_counter()
        time_min = datetime.datetime.utcnow()
        time_max = time_min + datetime.timedelta(hours=self.events_within_hours)
        events = []

        try:
            eventsResult = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMax=time_max.isoformat() + "Z",  # 'Z' indicates UTC time
                    timeMin=time_min.isoformat() + "Z",  # 'Z' indicates UTC time
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute(num_retries=5)
            )
        except Exception:
            return self.events or events
        else:
            for event in eventsResult.get("items", []):
                # filter out events that we did not accept (default)
                # unless we organized them with no attendees
                i_organized = event.get("organizer", {}).get("self", False)
                has_attendees = event.get("attendees", [])
                for attendee in event.get("attendees", []):
                    if attendee.get("self") is True:
                        if attendee["responseStatus"] in self.response:
                            break
                else:
                    # we did not organize the event or we did not accept it
                    if not i_organized or has_attendees:
                        continue

                # strip and lower case output if needed
                for key in ["description", "location", "summary"]:
                    event[key] = event.get(key, "").strip()
                    if self.force_lowercase is True:
                        event[key] = event[key].lower()

                # ignore all day events if configured
                if event["start"].get("date") is not None:
                    if self.ignore_all_day_events:
                        continue

                # filter out blacklisted event names
                if event["summary"] is not None:
                    if event["summary"].lower() in (
                        e.lower() for e in self.blacklist_events
                    ):
                        continue

                events.append(event)

        return events[: self.num_events]

    def _check_warn_threshold(self, time_to, event_dict):
        """
        Checks if the time until an event starts is less than or equal to the
        warn_threshold. If True, issue a warning with self.py3.notify_user.
        """
        if time_to["total_minutes"] <= self.warn_threshold:
            warn_message = self.py3.safe_format(self.format_notification, event_dict)
            self.py3.notify_user(warn_message, "warning", self.warn_timeout)

    def _gstr_to_date(self, date_str):
        """ Returns a dateime object from calendar date string."""
        return parser.parse(date_str).replace(tzinfo=tzlocal())

    def _gstr_to_datetime(self, date_time_str):
        """ Returns a datetime object from calendar date/time string."""
        return parser.parse(date_time_str)

    def _datetime_to_str(self, date_time, dt_format):
        """ Returns a strftime formatted string from a datetime object."""
        return date_time.strftime(dt_format)

    def _delta_time(self, date_time):
        """
        Returns in a dict the number of days/hours/minutes and total minutes
        until date_time.
        """
        now = datetime.datetime.now(tzlocal())
        diff = date_time - now

        days = int(diff.days)
        hours = int(diff.seconds / 3600)
        minutes = int((diff.seconds / 60) - (hours * 60)) + 1
        total_minutes = int((diff.seconds / 60) + (days * 24 * 60)) + 1

        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "total_minutes": total_minutes,
        }

    def _format_timedelta(self, index, time_delta, is_current):
        """
        Formats the dict time_to containing days/hours/minutes until an
        event starts into a composite according to time_to_formatted.

        Returns: A formatted composite.
        """
        time_delta_formatted = ""

        if time_delta["total_minutes"] <= self.time_to_max:
            time_delta_formatted = self.py3.safe_format(
                self.format_timer,
                {
                    "days": time_delta["days"],
                    "hours": time_delta["hours"],
                    "minutes": time_delta["minutes"],
                    "is_current": is_current,
                },
            )

        return time_delta_formatted

    def _build_response(self):
        """
        Builds the composite response to be output by the module by looping
        through all events and formatting the necessary strings.

        Returns: A composite containing the individual response for each event.
        """
        responses = []
        self.event_urls = []

        for index, event in enumerate(self.events):
            self.py3.threshold_get_color(index + 1, "event")
            self.py3.threshold_get_color(index + 1, "time")

            event_dict = {}

            event_dict["summary"] = event.get("summary")
            event_dict["location"] = event.get("location")
            event_dict["description"] = event.get("description")
            self.event_urls.append(
                event.get(self.preferred_event_link, event.get("htmlLink"))
            )

            if event["start"].get("date") is not None:
                start_dt = self._gstr_to_date(event["start"].get("date"))
                end_dt = self._gstr_to_date(event["end"].get("date"))
            else:
                start_dt = self._gstr_to_datetime(event["start"].get("dateTime"))
                end_dt = self._gstr_to_datetime(event["end"].get("dateTime"))

            if end_dt < datetime.datetime.now(tzlocal()):
                continue

            event_dict["start_time"] = self._datetime_to_str(start_dt, self.format_time)
            event_dict["end_time"] = self._datetime_to_str(end_dt, self.format_time)

            event_dict["start_date"] = self._datetime_to_str(start_dt, self.format_date)
            event_dict["end_date"] = self._datetime_to_str(end_dt, self.format_date)

            time_delta = self._delta_time(start_dt)
            if time_delta["days"] < 0:
                time_delta = self._delta_time(end_dt)
                is_current = True
            else:
                is_current = False

            event_dict["format_timer"] = self._format_timedelta(
                index, time_delta, is_current
            )

            if self.warn_threshold > 0:
                self._check_warn_threshold(time_delta, event_dict)

            event_formatted = self.py3.safe_format(
                self.format_event,
                {
                    "is_toggled": self.button_states[index],
                    "summary": event_dict["summary"],
                    "location": event_dict["location"],
                    "description": event_dict["description"],
                    "start_time": event_dict["start_time"],
                    "end_time": event_dict["end_time"],
                    "start_date": event_dict["start_date"],
                    "end_date": event_dict["end_date"],
                    "format_timer": event_dict["format_timer"],
                },
            )

            self.py3.composite_update(event_formatted, {"index": index})
            responses.append(event_formatted)

            self.no_update = False

        format_separator = self.py3.safe_format(self.format_separator)
        self.py3.composite_update(format_separator, {"index": "sep"})
        responses = self.py3.composite_join(format_separator, responses)

        return {"events": responses}

    def google_calendar(self):
        """
        The method that outputs the response.

        First, we check credential authorization. If no authorization, we
        display an error message, and try authorizing again in 5 seconds.

        Otherwise, we fetch the events, build the response, and output
        the resulting composite.
        """
        composite = {}

        if not self.is_authorized:
            cached_until = 0
            self.is_authorized = self._authorize_credentials()
        else:
            if not self.no_update:
                self.events = self._get_events()

            composite = self._build_response()
            cached_until = self.cache_timeout

        return {
            "cached_until": self.py3.time_in(cached_until),
            "composite": self.py3.safe_format(self.format, composite),
        }

    def on_click(self, event):
        if self.is_authorized and self.events is not None:
            """
            If button_refresh is clicked, we allow the events to be updated
            if the last event update occurred at least 1 second ago. This
            prevents a bug that can crash py3status since refreshing the
            module too fast results in incomplete event information being
            fetched as _get_events() is called repeatedly.

            Otherwise, we disable event updates.
            """
            self.no_update = True
            button = event["button"]
            button_index = event["index"]

            if button_index == "sep":
                self.py3.prevent_refresh()
            elif button == self.button_refresh:
                # wait before the next refresh
                if time.perf_counter() - self.last_update > 1:
                    self.no_update = False
            elif button == self.button_toggle:
                self.button_states[button_index] = not self.button_states[button_index]
            elif button == self.button_open:
                if self.event_urls:
                    self.py3.command_run(
                        self.browser_invocation.format(self.event_urls[button_index])
                    )
                self.py3.prevent_refresh()
            else:
                self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
