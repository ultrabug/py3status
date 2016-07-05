# -*- coding: utf-8 -*-
"""
Display information about the current song and video playing on player with
mpris support.

Configuration parameters:
    button_play: mouse button to play the entry
    button_stop: mouse button to stop the player
    button_pause: mouse button to pause the player
    button_pause_toggle: mouse button to toggle between play and pause mode
    button_next: mouse button to play the next entry
    button_previous: mouse button to play the previous entry
    color_paused: text color when song is paused, defaults to color_degraded
    color_playing: text color when song is playing, defaults to color_good
    color_stopped: text color when song is stopped, defaults to color_bad
    format: see placeholders below
    format_stream: see placeholders below, keep in mind that {artist} and
            {album} are empty. This format is also used for videos or just media
            files without an artist information!
    format_no_tags: define output if song informations couldn't read,
            keep in mind that this concerns only playceholders
            {artist}, {album}, {title} and {length}
    format_none: define output if no player is running
    state_paused: text for placeholder {state} when song is paused
    state_playing: text for placeholder {state} when song is playing
    state_stopped: text for placeholder {state} when song is stopped
    shuffle_on: text for placeholder {shuffle} when shuffle mode is activated
    shuffle_off: text for placeholder {shuffle} when shuffle mode is deactivated
    loop_none: text for placeholder {loop} when loop mode is deactivated
    loop_track: text for placeholder {loop} when loop mode is in track mode
    loop_playlist: text for placeholder {loop} when loop mode is in playlist mode
    player_priority: priority of the players.
            Keep in mind that the state has a higher priority than
            player_priority. So when player_priority is "mpd,bomi" and mpd is
            paused and bomi is playing than bomi wins.

Format of status string placeholders:
    {album} album name
    {artist} artiste name (first one)
    {date} creation date of the song
    {genre} the genre
    {length} time duration of the song
    {loop} show if loop mode is activated or not
    {player} show name of the player
    {shuffle} show if shuffle mode is activated or not
    {state} playback status of the player
    {time} played time of the song
    {time_left} time left before song end
    {title} name of the song
    {track} track number of the song

i3status.conf example:

```
mpris {
    format = "{player}: {state} {artist} - {title} [{time} / {length}]"
    format_stream = "{player}: {state} {title} [{time} / {length}]"
    format_none = "no player"
    format_no_tags = "{player}: {state} Unknown"
    player_priority = "mpd,cantata,vlc,bomi,*"
}
```

only show information from vlc:

```
mpris {
    player_priority = "vlc"
}
```

only show information from mpd and vlc, but mpd has a higher priority:

```
mpris {
    player_priority = "mpd,vlc"
}
```

show information of all players, but mpd and vlc have the highest priority:

```
mpris {
    player_priority = "mpd,vlc,*"
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
UNKNOWN = 'Unknown'
UNKNOWN_TIME = '-:--'


def _get_time_str(microseconds):
    seconds = int(microseconds / 1000000)
    time = str(timedelta(seconds=seconds))
    if time[0] == '0':
        time = time[2:]
        if time[0] == '0':
            time = time[1:]

    return time


class Py3status:
    """
    """
    # available configuration parameters
    button_play = None
    button_stop = None
    button_pause = None
    button_pause_toggle = 1
    button_next = 4
    button_previous = 5
    color_paused = None
    color_playing = None
    color_stopped = None
#    format = '{state} {artist} - {title}'
    format = 'FORMAT: player:{player}, state:{state}, artist:{artist}, title:{title}, album:{album}, date:{date}, genre:{genre}, length:{length}, time:{time}, time_left:{time_left}, shuffle:{shuffle}, loop:{loop}'
#    format_stream = '{state} {title}'
    format_stream = 'STREAM: player:{player}, state:{state}, artist:{artist}, title:{title}, album:{album}, date:{date}, genre:{genre}, length:{length}, time:{time}, time_left:{time_left}, shuffle:{shuffle}, loop:{loop}'
#    format_no_tags = '{state} Unknown'
    format_no_tags = 'NO_TAGS: player:{player}, state:{state}, artist:{artist}, title:{title}, album:{album}, date:{date}, genre:{genre}, length:{length}, time:{time}, time_left:{time_left}, shuffle:{shuffle}, loop:{loop}'
    format_none = 'no player running'
    state_paused = '▮▮'
    state_playing = '▶'
    state_stopped = '◾'
    shuffle_off = '⇉'
    shuffle_on = '⤨'
    loop_none = '⇥'
    loop_track = '⟲'
    loop_playlist = '⟳'
#    player_priority = None
    player_priority = "mpd,vlc,bomi,*"

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

    def _get_state_format(self, i3s_config):
        playback_status = self._player.PlaybackStatus

        if playback_status == 'Playing':
            color = self.color_playing or i3s_config['color_good']
            state = self.state_playing
        elif playback_status == 'Paused':
            color = self.color_paused or i3s_config['color_degraded']
            state = self.state_paused
        else:
            color = self.color_stopped or i3s_config['color_bad']
            state = self.state_stopped

        return (color, state)

    def _get_loop_format(self):
        loop_status = self._player.LoopStatus

        if loop_status == 'Track':
            return self.loop_track
        elif loop_status == 'Playlist':
            return self.loop_playlist
        else:
            return self.loop_none

    def _get_metadata(self, metadata):
        is_stream = 'file://' not in metadata.get('xesam:url')
        album = metadata.get('xesam:album') or UNKNOWN
        date = metadata.get('xesam:contentCreated') or UNKNOWN
        track = metadata.get('xesam:trackNumber') or UNKNOWN
        title = metadata.get('xesam:title') or UNKNOWN
        length = metadata.get('mpris:length')

        if metadata.get('xesam:genre') is not None:
            genre = metadata.get('xesam:genre')[0]
        else:
            genre = UNKNOWN

        if metadata.get('xesam:artist') is not None:
            artist = metadata.get('xesam:artist')[0]
        else:
            artist = UNKNOWN
            # we assume here that we playing a video and these types of media we
            # handle just like streams
            is_stream = True

        return (album, artist, date, genre, length, track, title, is_stream)

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
            if '*' in player_priority:
                players_prioritized += players

        for player_name in players_prioritized:
            player_state = self._get_state(player_name)

            if player_state == 'Playing':
                return player_name
            elif player_state == 'Paused':
                players_paused.append(player_name)
            else:
                players_stopped.append(player_name)

        if players_paused:
            return players_paused[0]
        if players_stopped:
            return players_stopped[0]

        return 'None'

    def _get_text(self, i3s_config):
        """
        Get the current metadatas
        """
        is_stream = False
        player = UNKNOWN
        state = UNKNOWN
        artist = UNKNOWN
        album = UNKNOWN
        date = UNKNOWN
        genre = UNKNOWN
        length = UNKNOWN_TIME
        time = UNKNOWN_TIME
        time_left = UNKNOWN_TIME
        title = UNKNOWN
        track = '?'

        if self._player is None:
            return (self.format_none, i3s_config['color_bad'])

        try:
            player = self._player.Identity
            (color, state) = self._get_state_format(i3s_config)
            shuffle = self.shuffle_on if self._player.Shuffle else self.shuffle_off
            loop = self._get_loop_format()

            _time_ms = self._player.Position
            time = _get_time_str(_time_ms)

            metadata = self._player.Metadata
            has_metadata = len(metadata) > 0
            if has_metadata:
                # TODO: Format this
                (album, artist, date, genre, _length_ms, track, title,
                 is_stream) = self._get_metadata(metadata)

                if _length_ms is not None:
                    length = _get_time_str(_length_ms)
                    _time_left_ms = _length_ms - _time_ms
                    time_left = _get_time_str(_time_left_ms)

        except Exception:
            color = i3s_config['color_bad']

        if not has_metadata:
            format = self.format_no_tags
        elif is_stream:
            # Delete the file extension
            title = re.sub(r'\....$', '', title)
            format = self.format_stream
        else:
            format = self.format

        return (format.format(player=player,
                              state=state,
                              loop=loop,
                              shuffle=shuffle,
                              album=album,
                              artist=artist,
                              date=date,
                              genre=genre,
                              length=length,
                              time=time,
                              time_left=time_left,
                              title=title,
                              track=track), color)

    def mpris(self, i3s_output_list, i3s_config):
        """
        Get the current "artist - title" and return it.
        """
        self._dbus = SessionBus()

        running_player = self._detect_running_player()
        self._player = self._get_player(running_player)

        (text, color) = self._get_text(i3s_config)
        response = {
            'cached_until': time() + i3s_config['interval'],
            'full_text': text,
            'color': color
        }

        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Handles click events
        """
        button = event['button']

        if button == self.button_play:
            self._player.Play()
        elif button == self.button_stop:
            self._player.Stop()
        elif button == self.button_pause:
            self._player.Pause()
        elif button == self.button_pause_toggle:
            self._player.PlayPause()
        elif button == self.button_next:
            self._player.Next()
        elif button == self.button_previous:
            self._player.Previous()


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
