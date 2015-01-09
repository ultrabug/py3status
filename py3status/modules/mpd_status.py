# -*- coding: utf-8 -*-
"""
Mpd - module to show information from mpd in your i3bar.
Reequires
    - python-mpd2 (NOT python2-mpd2)
    # pip install python-mpd2

@author shadowprince
@license Eclipse Public License
"""

import re
from mpd import (MPDClient, CommandError)
from socket import error as SocketError
from time import time

# state characters (or strings). Actual of them replaces {state} placeholder in self.format
STATE_CHARACTERS = {
    "pause": "[pause]",
    "play": "[play]",
    "stop": "[stop]",
}


class Py3status:
    """
    Configuration parameters:
        - format : indicator text format
        - hide_when_paused / hide_when_stopped : hide any indicator, if
        - host : mpd host
        - max_width : if text length will be greater - it'll shrink it
        - password : mpd password
        - port : mpd port

    Format of result string can contain:
        {state} - current state from STATE_CHARACTERS
        Track information:
        {track}, {artist}, {title}, {time}, {album}, {pos}
        In additional, information about next track also comes in,
        in analogue with current, but with next_ prefix, like {next_title}
    """

    # available configuration parameters
    cache_timeout = 2
    color = None
    format = '{state} №{pos}. {artist} - {title} [{time}] | {next_title}'
    hide_when_paused = False
    hide_when_stopped = True
    host = 'localhost'
    max_width = 120
    password = None
    port = '6600'

    def __init__(self):
        self.text = ''

    def current_track(self, i3s_output_list, i3s_config):
        try:
            c = MPDClient()
            c.connect(host=self.host, port=self.port)
            if self.password:
                c.password(self.password)

            status = c.status()
            song = int(status.get("song", 0))
            next_song = int(status.get("nextsong", 0))

            if (status["state"] == "pause" and self.hide_when_paused) or (status["state"] == "stop" and self.hide_when_stopped):
                text = ""
            else:
                try:
                    song = c.playlistinfo()[song]
                    song["time"] = "{0:.2f}".format(int(song.get("time", 1)) / 60)
                except IndexError:
                    song = {}

                try:
                    next_song = c.playlistinfo()[next_song]
                except IndexError:
                    next_song = {}

                format_args = song
                format_args["state"] = STATE_CHARACTERS.get(status.get("state", None))
                for k, v in next_song.items():
                    format_args["next_{}".format(k)] = v

                text = self.format
                for k, v in format_args.items():
                    text = text.replace("{" + k + "}", v)

                for sub in re.findall(r"{\S+?}", text):
                    text = text.replace(sub, "")
        except SocketError:
            text = "Failed to connect to mpd!"
        except CommandError:
            text = "Failed to authenticate to mpd!"
            c.disconnect()

        if len(text) > self.max_width:
            text = text[-self.max_width-3:] + "..."

        if self.text != text:
            transformed = True
            self.text = text
        else:
            transformed = False

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': self.text,
            'transformed': transformed
        }

        if self.color:
            response['color'] = self.color

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.current_track([], {}))
        sleep(1)
