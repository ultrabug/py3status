# -*- coding: utf-8 -*-
"""
Display song currently playing in Spotify.

Configuration parameters:
    cache_timeout: how often to update the bar (default 5)
    format: see placeholders below (default '{artist} : {title}')
    format_down: define output if spotify is not running
        (default 'Spotify not running')
    format_stopped: define output if spotify is not playing
        (default 'Spotify stopped')

Format placeholders:
    {album} album name
    {artist} artiste name (first one)
    {time} time duration of the song
    {title} name of the song

Color options:
    color_offline: Spotify is not running, defaults to color_bad
    color_paused: Song is stopped or paused, defaults to color_degraded
    color_playing: Song is playing, defaults to color_good

i3status.conf example:

```
spotify {
    format = "{title} by {artist} -> {time}"
    format_down = "no Spotify"
}
```

Requires:
        spotify (>=1.0.27.71.g0a26e3b2)

@author Pierre Guilbert, Jimmy Garpehäll, sondrele, Andrwe

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'Rick Astley : Never Gonna Give You Up'}

paused
{'color': '#FFFF00', 'full_text': 'Rick Astley : Never Gonna Give You Up'}

stopped
{'color': '#FF0000', 'full_text': 'Spotify stopped'}
"""

from datetime import timedelta
import dbus


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = '{artist} : {title}'
    format_down = 'Spotify not running'
    format_stopped = 'Spotify stopped'

    def _get_text(self):
        """
        Get the current song metadatas (artist - title)
        """
        bus = dbus.SessionBus()
        try:
            self.__bus = bus.get_object('org.mpris.MediaPlayer2.spotify',
                                        '/org/mpris/MediaPlayer2')
            self.player = dbus.Interface(
                self.__bus, 'org.freedesktop.DBus.Properties')

            try:
                metadata = self.player.Get('org.mpris.MediaPlayer2.Player',
                                           'Metadata')
                album = metadata.get('xesam:album')
                artist = metadata.get('xesam:artist')[0]
                microtime = metadata.get('mpris:length')
                rtime = str(timedelta(microseconds=microtime))[:-7]
                title = metadata.get('xesam:title')
                playback_status = self.player.Get(
                    'org.mpris.MediaPlayer2.Player', 'PlaybackStatus'
                )
                if playback_status.strip() == 'Playing':
                    color = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
                else:
                    color = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
            except Exception:
                return (
                    self.format_stopped,
                    self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED)

            return (
                self.py3.safe_format(
                    self.format,
                    dict(title=title,
                         artist=artist,
                         album=album,
                         time=rtime)
                ), color)
        except Exception:
            return (
                self.format_down,
                self.py3.COLOR_OFFLINE or self.py3.COLOR_BAD)

    def spotify(self):
        """
        Get the current "artist - title" and return it.
        """
        (text, color) = self._get_text()
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': text,
            'color': color
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
