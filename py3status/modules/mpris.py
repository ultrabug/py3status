# -*- coding: utf-8 -*-
"""
Display information about the current song and video playing on player with
mpris support.

Configuration parameters:
    color_paused: text color when song is paused, defaults to color_degraded
    color_playing: text color when song is playing, defaults to color_good
    color_stopped: text color when song is stopped, defaults to color_bad
    format: see placeholders below
    format_video: see placeholders below, keep in mind that {artist} and {album}
            are empty
    format_error: define output if one or more informations couldn't read,
            keep in mind that some playceholders may be work
    format_none: define output if no player is running
    state_paused: text for placeholder {state} when song is paused
    state_playing: text for placeholder {state} when song is playing
    state_stopped: text for placeholder {state} when song is stopped
    player_priority: priority of the players.
            Keep in mind that the state has a higher priority than
            player_priority. So when player_priority is "mpd,bomi" and mpd is
            paused and bomi is playing than bomi wins.

Format of status string placeholders:
    {state} playback status of the player
    {album} album name
    {artist} artiste name (first one)
    {time} time duration of the song
    {title} name of the song

i3status.conf example:

```
mpris {
    format = "{state} {artist} - {title} -> {time}"
    format_video = "{state} {title} -> {time}"
    format_none = "no player"
    format_error = "{state} Unknown"
    player_priority = "mpd,cantata,vlc,bomi"
}
```

Requires:
    pydbus

@author Pierre Guilbert, Jimmy Garpehäll, sondrele, Andrwe, Moritz Lüdecke
"""

from datetime import timedelta
from time import time, sleep
import re
from pydbus import SessionBus


SERVICE_BUS = 'org.mpris.MediaPlayer2'
INTERFACE = SERVICE_BUS + '.Player'
SERVICE_BUS_URL = '/org/mpris/MediaPlayer2'
SERVICE_BUS_REGEX = '^' + re.sub(r'\.', '\.', SERVICE_BUS) + '.'


class Py3status:
    """
    """
    # available configuration parameters
    color_paused = None
    color_playing = None
    color_stopped = None
    format = '{state} {artist} - {title}'
    format_video = '{state} {title}'
    format_error = 'no player running'
    format_none = 'no player running'
    state_paused = '▮▮'
    state_playing = '▶'
    state_stopped = '◾'
    player_priority = None

    def _get_player(self, player):
        """
        Get dbus object
        """
        try:
            return self._dbus.get(SERVICE_BUS + '.%s' % player, SERVICE_BUS_URL)
        except Exception:
            return None

    def _get_state(self, player):
        """
        Get the state of a player
        """
        player = self._get_player(player)
        if player is None:
            return 'None'

        return player.PlaybackStatus

    def _detect_running_player(self):
        """
        Detect running player process, if any
        """
        players_paused = []
        players_stopped = []
        players = []
        players_prioritized = []

        _dbus = self._dbus.get('org.freedesktop.DBus')
        for player in _dbus.ListNames():
            if SERVICE_BUS in player:
                player = re.sub(r'%s' % SERVICE_BUS_REGEX, '', player)
                players.append(player)

        if self.player_priority is None:
            players_prioritized = players
        else:
            player_priority = self.player_priority.split(',')

            for player_name in player_priority:
                if player_name in players:
                    players.remove(player_name)
                    players_prioritized.append(player_name)
            players_prioritized += players

        for player_name in players_prioritized:
            player_state = self._get_state(player_name)

            if player_state == 'Playing':
                return player_name
            elif player_state == 'Paused':
                players_paused.append(player_name)
            elif player_state == 'Stopped':
                players_stopped.append(player_name)

        if players_paused:
            return players_paused[0]
        if players_stopped:
            return players_stopped[0]

        return 'None'

    def _get_text(self, i3s_config, player):
        """
        Get the current metadatas
        """
        is_video = False
        album = 'Unknown'
        artist = 'Unknown'
        state = 'Unkown'
        title = 'Unknown'
        rtime = '0'

        player = self._get_player(player)
        if player is None:
            return (self.format_none, i3s_config['color_bad'])

        try:
            metadata = player.Metadata
            playback_status = player.PlaybackStatus

            if playback_status.strip() == 'Playing':
                color = self.color_playing or i3s_config['color_good']
                state = self.state_playing
            elif playback_status.strip() == 'Paused':
                color = self.color_paused or i3s_config['color_degraded']
                state = self.state_paused
            else:
                color = self.color_stopped or i3s_config['color_bad']
                state = self.state_stopped

            try:
                album = metadata.get('xesam:album')
                artist = metadata.get('xesam:artist')[0]
            except Exception:
                is_video = True

            microtime = metadata.get('mpris:length')
            rtime = str(timedelta(microseconds=microtime))[:-7]
            title = metadata.get('xesam:title')
        except Exception:
            return (self.format_error.format(state=state,
                                             title=title,
                                             artist=artist,
                                             album=album,
                                             time=rtime),
                    i3s_config['color_bad'])

        if is_video:
            title = re.sub(r'\....$', '', title)
            return (self.format_video.format(state=state,
                                             title=title,
                                             time=rtime), color)
        else:
            return (self.format.format(state=state,
                                       title=title,
                                       artist=artist,
                                       album=album,
                                       time=rtime), color)

    def mpris(self, i3s_output_list, i3s_config):
        """
        Get the current "artist - title" and return it.
        """
        self._dbus = SessionBus()

        running_player = self._detect_running_player()
        (text, color) = self._get_text(i3s_config, running_player)
        response = {
            'cached_until': time() + i3s_config['interval'],
            'full_text': text,
            'color': color
        }

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    x = Py3status()
    config = {
        'interval': 5,
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }

    while True:
        print(x.mpris([], config))
        sleep(1)
