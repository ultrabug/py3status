# -*- coding: utf-8 -*-

import re

from mpd import (MPDClient, CommandError)
from socket import error as SocketError
from time import time

"""
Mpd - module to show information from mpd to your's bar! Settings listed above.
Reequires
    - python-mpd2 (NOT python2-mpd2)
    # pip install python-mpd2

@author shadowprince
@license Eclipse Public License
"""

# mpd settings
HOST = "localhost"
PORT = "6600"
PASSWORD = None

# time to update
CACHE_TIMEOUT = 1

# position
POSITION = 0

# if text length will be greater - it'll shrink it
MAX_WIDTH = 120

# hide any indicator, if
HIDE_WHEN_PAUSED = False
HIDE_WHEN_STOPPED = True

# state characters (or strings). Actual of them replaces {state} placeholder in STRFORMAT
STATE_CHARACTERS = {
    "pause": "[pause]",
    "play": "[play]",
    "stop": "[stop]",
}

""" format of result string
can contain:
    {state} - current state from STATE_CHARACTERS
    Track information:
    {track}, {artist}, {title}, {time}, {album}, {pos}
    In additional, information about next track also comes in, in analogue with current, but with next_ prefix,
    like {next_title}
"""
STRFORMAT = "{state} №{pos}. {artist} - {title} [{time}] | {next_title}"


class Py3status:
    def __init__(self):
        self.text = ''

    def currentTrack(self, i3status_output_json, i3status_config):
        try:
            c = MPDClient()
            c.connect(host=HOST, port=PORT)
            if PASSWORD:
                c.password(PASSWORD)

            status = c.status()
            song = int(status.get("song", 0))
            next_song = int(status.get("nextsong", 0))

            if (status["state"] == "pause" and HIDE_WHEN_PAUSED) or (status["state"] == "stop" and HIDE_WHEN_STOPPED):
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

                text = STRFORMAT
                for k, v in format_args.items():
                    text = text.replace("{" + k + "}", v)

                for sub in re.findall(r"{\S+?}", text):
                    text = text.replace(sub, "")
        except SocketError:
            text = "Failed to connect to mpd!"
        except CommandError:
            text = "Failed to authenticate to mpd!"
            c.disconnect()

        if len(text) > MAX_WIDTH:
            text = text[-MAX_WIDTH-3:] + "..."

        if self.text != text:
            transformed = True
            self.text = text
        else:
            transformed = False

        response = {
            'cached_until': time() + CACHE_TIMEOUT,
            'full_text': self.text,
            'name': 'scratchpad-count',
            'transformed': transformed
        }

        return (POSITION, response)
