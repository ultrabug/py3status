"""
Display song currently playing in Spotify.

Configuration parameters:
    button_next: button to switch to next song (default None)
    button_play_pause: button to toggle play/pause (default None)
    button_previous: button to switch to previous song (default None)
    cache_timeout: how often to update the bar (default 5)
    dbus_client: Used to override which app is used as a client for
        spotify. If you use spotifyd as a client, set this to
        'org.mpris.MediaPlayer2.spotifyd'
        (default 'org.mpris.MediaPlayer2.spotify')
    format: see placeholders below (default '{artist} : {title}')
    format_down: define output if spotify is not running
        (default 'Spotify not running')
    format_stopped: define output if spotify is not playing
        (default 'Spotify stopped')
    sanitize_titles: whether to remove meta data from album/track title
        (default True)
    sanitize_words: which meta data to remove
        *(default ['bonus', 'demo', 'edit', 'explicit', 'extended',
            'feat', 'mono', 'remaster', 'stereo', 'version'])*

Format placeholders:
    {album} album name
    {artist} artiste name (first one)
    {playback} state of the playback: Playing, Paused
    {time} time duration of the song
    {title} name of the song

Color options:
    color_offline: Spotify is not running, defaults to color_bad
    color_paused: Song is stopped or paused, defaults to color_degraded
    color_playing: Song is playing, defaults to color_good

Requires:
    python-dbus: to access dbus in python
    spotify: a proprietary music streaming service

Examples:
```
spotify {
    button_next = 4
    button_play_pause = 1
    button_previous = 5
    format = "{title} by {artist} -> {time}"
    format_down = "no Spotify"
}
```

@author Pierre Guilbert, Jimmy Garpehäll, sondrele, Andrwe

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'Rick Astley : Never Gonna Give You Up'}

paused
{'color': '#FFFF00', 'full_text': 'Rick Astley : Never Gonna Give You Up'}

stopped
{'color': '#FF0000', 'full_text': 'Spotify stopped'}
"""

import re
from datetime import timedelta
from time import sleep

import dbus

SPOTIFY_CMD = """dbus-send --print-reply --dest={dbus_client}
                 /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.{cmd}"""


class Py3status:
    """
    """

    # available configuration parameters
    button_next = None
    button_play_pause = None
    button_previous = None
    cache_timeout = 5
    dbus_client = "org.mpris.MediaPlayer2.spotify"
    format = "{artist} : {title}"
    format_down = "Spotify not running"
    format_stopped = "Spotify stopped"
    sanitize_titles = True
    sanitize_words = [
        "bonus",
        "demo",
        "edit",
        "explicit",
        "extended",
        "feat",
        "mono",
        "remaster",
        "stereo",
        "version",
    ]

    def _spotify_cmd(self, action):
        return SPOTIFY_CMD.format(dbus_client=self.dbus_client, cmd=action)

    def post_config_hook(self):
        """
        """
        # Match string after hyphen, comma, semicolon or slash containing any metadata word
        # examples:
        # - Remastered 2012
        # / Radio Edit
        # ; Remastered
        self.after_delimiter = self._compile_re(
            r"([\-,;/])([^\-,;/])*(META_WORDS_HERE).*"
        )

        # Match brackets with their content containing any metadata word
        # examples:
        # (Remastered 2017)
        # [Single]
        # (Bonus Track)
        self.inside_brackets = self._compile_re(
            r"([\(\[][^)\]]*?(META_WORDS_HERE)[^)\]]*?[\)\]])"
        )

    def _compile_re(self, expression):
        """
        Compile given regular expression for current sanitize words
        """
        meta_words = "|".join(self.sanitize_words)
        expression = expression.replace("META_WORDS_HERE", meta_words)
        return re.compile(expression, re.IGNORECASE)

    def _get_text(self):
        """
        Get the current song metadatas (artist - title)
        """
        bus = dbus.SessionBus()
        try:
            self.__bus = bus.get_object(self.dbus_client, "/org/mpris/MediaPlayer2")
            self.player = dbus.Interface(self.__bus, "org.freedesktop.DBus.Properties")

            try:
                metadata = self.player.Get("org.mpris.MediaPlayer2.Player", "Metadata")
                album = metadata.get("xesam:album")
                artist = metadata.get("xesam:artist")[0]
                microtime = metadata.get("mpris:length")
                rtime = str(timedelta(seconds=microtime // 1_000_000))
                title = metadata.get("xesam:title")
                if self.sanitize_titles:
                    album = self._sanitize_title(album)
                    title = self._sanitize_title(title)

                playback_status = self.player.Get(
                    "org.mpris.MediaPlayer2.Player", "PlaybackStatus"
                )
                if playback_status == "Playing":
                    color = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
                else:
                    color = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
            except Exception:
                return (
                    self.format_stopped,
                    self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED,
                )

            return (
                self.py3.safe_format(
                    self.format,
                    dict(
                        title=title,
                        artist=artist,
                        album=album,
                        time=rtime,
                        playback=playback_status,
                    ),
                ),
                color,
            )
        except Exception:
            return (self.format_down, self.py3.COLOR_OFFLINE or self.py3.COLOR_BAD)

    def _sanitize_title(self, title):
        """
        Remove redundant metadata from title and return it
        """
        title = re.sub(self.inside_brackets, "", title)
        title = re.sub(self.after_delimiter, "", title)
        return title.strip()

    def spotify(self):
        """
        Get the current "artist - title" and return it.
        """
        (text, color) = self._get_text()
        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": color,
            "full_text": text,
        }
        return response

    def on_click(self, event):
        """
        """
        button = event["button"]
        if button == self.button_play_pause:
            self.py3.command_run(self._spotify_cmd("PlayPause"))
            sleep(0.1)
        elif button == self.button_next:
            self.py3.command_run(self._spotify_cmd("Next"))
            sleep(0.1)
        elif button == self.button_previous:
            self.py3.command_run(self._spotify_cmd("Previous"))
            sleep(0.1)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
