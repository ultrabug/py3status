# -*- coding: utf-8 -*-
"""
Display song currently playing in mpd.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 2)
    format: template string (see below)
        (default '{state} [[[{artist}] - {title}]|[{file}]]')
    hide_on_error: hide the status if an error has occurred (default False)
    hide_when_paused: hide the status if state is paused (default False)
    hide_when_stopped: hide the status if state is stopped (default True)
    host: mpd host (default 'localhost')
    max_width: maximum status length (default 120)
    password: mpd password (default None)
    port: mpd port (default '6600')
    state_pause: label to display for "paused" state (default '[pause]')
    state_play: label to display for "playing" state (default '[play]')
    state_stop: label to display for "stopped" state (default '[stop]')

Format placeholders:
    {state} state (paused, playing. stopped) can be defined via `state_..`
        configuration parameters
    Refer to the mpc(1) manual page for the list of available placeholders to
    be used in the format.  Placeholders should use braces `{}` rather than
    percent `%%` eg `{artist}`.
    Every placeholder can also be prefixed with
    `next_` to retrieve the data for the song following the one currently
    playing.

Color options:
    color_pause: Paused, default color_degraded
    color_play: Playing, default color_good
    color_stop: Stopped, default color_bad

Requires:
    python-mpd2: (NOT python2-mpd2)

Examples:
```
# Show state and (artist -) title, if no title fallback to file:
{state} [[[{artist} - ]{title}]|[{file}]]

# Show state, [duration], title (or file) and next song title (or file):
{state} \[{time}\] [{title}|{file}] → [{next_title}|{next_file}]
```

@author shadowprince, zopieux
@license Eclipse Public License

SAMPLE OUTPUT
{'color': '#00ff00', 'full_text': '[play] Music For Programming - Idol Eyes'}

paused
{'color': '#ffff00', 'full_text': '[pause] Music For Programming - Idol Eyes'}

stopped
{'color': '#ff0000', 'full_text': '[stop] Music For Programming - Idol Eyes'}
"""

import datetime
import re
import socket
from py3status.composite import Composite
from mpd import MPDClient, CommandError, ConnectionError


def song_attr(song, attr):
    def parse_mtime(date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    if attr == "time":
        try:
            duration = int(song["time"])
            if duration > 0:
                minutes, seconds = divmod(duration, 60)
                return "{:d}:{:02d}".format(minutes, seconds)
            raise ValueError
        except (KeyError, ValueError):
            return ""
    elif attr == "position":
        try:
            return "{}".format(int(song["pos"]) + 1)
        except (KeyError, ValueError):
            return ""
    elif attr == "mtime":
        return parse_mtime(song["last-modified"]).strftime("%c")
    elif attr == "mdate":
        return parse_mtime(song["last-modified"]).strftime("%x")

    return song.get(attr, "")


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 2
    format = "{state} [[[{artist}] - {title}]|[{file}]]"
    hide_on_error = False
    hide_when_paused = False
    hide_when_stopped = True
    host = "localhost"
    max_width = 120
    password = None
    port = "6600"
    state_pause = "[pause]"
    state_play = "[play]"
    state_stop = "[stop]"

    def post_config_hook(self):
        # Convert from %placeholder% to {placeholder}
        # This is not perfect but should be good enough
        if not self.py3.get_placeholders_list(self.format) and "%" in self.format:
            self.format = re.sub("%([a-z]+)%", r"{\1}", self.format)
            self.py3.log("Old % style format DEPRECATED use { style format")
        # class variables:
        self.client = None

    def _get_mpd(self, disconnect=False):
        if disconnect:
            try:
                self.client.disconnect()
            finally:
                self.client = None
            return

        try:
            if self.client is None:
                self.client = MPDClient()
                self.client.connect(host=self.host, port=self.port)
                if self.password:
                    self.client.password(self.password)
            return self.client
        except (socket.error, ConnectionError, CommandError) as e:
            self.client = None
            raise e

    def _state_character(self, state):
        if state == "play":
            return self.state_play
        elif state == "pause":
            return self.state_pause
        elif state == "stop":
            return self.state_stop
        return "?"

    def mpd_status(self):
        try:
            status = self._get_mpd().status()
            song = int(status.get("song", 0))
            next_song = int(status.get("nextsong", 0))

            state = status.get("state")

            if (state == "pause" and self.hide_when_paused) or (
                state == "stop" and self.hide_when_stopped
            ):
                text = ""

            else:
                playlist_info = self._get_mpd().playlistinfo()
                try:
                    song = playlist_info[song]
                except IndexError:
                    song = {}
                try:
                    next_song = playlist_info[next_song]
                except IndexError:
                    next_song = {}

                song["state"] = next_song["state"] = self._state_character(state)

                def attr_getter(attr):
                    if attr.startswith("next_"):
                        return song_attr(next_song, attr[5:])
                    return song_attr(song, attr)

                text = self.py3.safe_format(self.format, attr_getter=attr_getter)
                if isinstance(text, Composite):
                    text = text.text()

        except ValueError:
            # when status.get(...) returns None; e.g. during reversal of playlist
            text = "No song information!"
            state = None
        except socket.error:
            text = "Failed to connect to mpd!"
            state = None
        except ConnectionError:
            text = "Error while connecting to mpd!"
            state = None
            self._get_mpd(disconnect=True)
        except CommandError:
            text = "Failed to authenticate to mpd!"
            state = None
            self._get_mpd(disconnect=True)

        if len(text) > self.max_width:
            text = u"{}...".format(text[: self.max_width - 3])

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": text if state or not self.hide_on_error else "",
        }

        if state:
            if state == "play":
                response["color"] = self.py3.COLOR_PLAY or self.py3.COLOR_GOOD
            elif state == "pause":
                response["color"] = self.py3.COLOR_PAUSE or self.py3.COLOR_DEGRADED
            elif state == "stop":
                response["color"] = self.py3.COLOR_STOP or self.py3.COLOR_BAD

        return response

    def kill(self):
        self._get_mpd(disconnect=True)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
