# -*- coding: utf-8 -*-
"""
Display information about the current song and video playing on player with
mpris support.

There are two ways to control the media player. Either by clicking with a mouse
button in the text information or by using show_controls. For former you have
to define the button parameters in the i3status config.

Configuration parameters:
    button_stop: mouse button to stop the player
    button_toggle: mouse button to toggle between play and pause mode
    button_next: mouse button to play the next entry
    button_previous: mouse button to play the previous entry
    buttons_order: order of the buttons play, pause, toggle, stop, next and
            previous
    color_paused: text color when song is paused, defaults to color_degraded
    color_playing: text color when song is playing, defaults to color_good
    color_stopped: text color when song is stopped, defaults to color_bad
    format: see placeholders below
    format_stream: see placeholders below, keep in mind that {artist} and
            {album} are empty. This format is also used for videos or just media
            files without an artist information or any other metadata!
    format_none: define output if no player is running
    icon_pause: text for the pause button in the button control panel
    icon_play: text for the play button in the button control panel
    icon_stop: text for the stop button in the button control panel
    icon_next: text for the next button in the button control panel
    icon_previous: text for the previous button in the button control panel
    show_controls: where to show the control buttons (see buttons_order).
            Can be left, right or none
    state_pause: text for placeholder {state} when song is paused
    state_play: text for placeholder {state} when song is playing
    state_stop: text for placeholder {state} when song is stopped
    player_priority: priority of the players.
            Keep in mind that the state has a higher priority than
            player_priority. So when player_priority is "mpd,bomi" and mpd is
            paused and bomi is playing than bomi wins.

Format of status string placeholders:
    {album} album name
    {artist} artiste name (first one)
    {length} time duration of the song
    {player} show name of the player
    {state} playback status of the player
    {time} played time of the song
    {title} name of the song

i3status.conf example:

```
mpris {
    format = "{player}: {state} {artist} - {title} [{time} / {length}]"
    format_stream = "{player}: {state} {title} [{time} / {length}]"
    format_none = "no player"
    show_controls = "left"
    buttons_order = "previous,play,next"
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
from time import time
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
    button_stop = None
    button_toggle = 1
    button_next = 4
    button_previous = 5
    buttons_order = 'previous,toggle,next'
    color_paused = None
    color_playing = None
    color_stopped = None
    format = '{state} {artist} - {title}'
    format_stream = '{state} {title}'
    format_none = 'no player running'
    icon_pause = ' ▮▮ '
    icon_play = ' ▶ '
    icon_stop = ' ◾ '
    icon_next = ' » '
    icon_previous = ' « '
    show_controls = None
    state_pause = '▮▮'
    state_play = '▶'
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

    def _get_state_format(self, i3s_config):
        playback_status = self._player.PlaybackStatus

        if playback_status == 'Playing':
            color = self.color_playing or i3s_config['color_good']
            state = self.state_play
        elif playback_status == 'Paused':
            color = self.color_paused or i3s_config['color_degraded']
            state = self.state_pause
        else:
            color = self.color_stopped or i3s_config['color_bad']
            state = self.state_stop

        return (color, state)

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
        length = UNKNOWN_TIME
        time = UNKNOWN_TIME
        title = UNKNOWN

        try:
            player = self._player.Identity
            (color, state) = self._get_state_format(i3s_config)

            _time_ms = self._player.Position
            time = _get_time_str(_time_ms)

            metadata = self._player.Metadata
            if len(metadata) > 0:
                url = metadata.get('xesam:url')
                is_stream = url is not None and 'file://' not in url
                title = metadata.get('xesam:title') or UNKNOWN
                album = metadata.get('xesam:album') or UNKNOWN

                if metadata.get('xesam:artist') is not None:
                    artist = metadata.get('xesam:artist')[0]
                else:
                    # we assume here that we playing a video and these types of
                    # media we handle just like streams
                    is_stream = True

                _length_ms = metadata.get('mpris:length')
                if _length_ms is not None:
                    length = _get_time_str(_length_ms)
            else:
                # use stream format if no metadata is available
                is_stream = True
        except Exception:
            color = i3s_config['color_bad']

        if is_stream:
            # delete the file extension
            title = re.sub(r'\....$', '', title)
            format = self.format_stream
        else:
            format = self.format

        return (format.format(player=player,
                              state=state,
                              album=album,
                              artist=artist,
                              length=length,
                              time=time,
                              title=title), color)

    def _get_control_states(self):
        control_states = {
            'pause':    {'clickable': 'CanPause',
                         'icon':      self.icon_pause,
                         'action':    'Pause'},
            'play':     {'clickable': 'CanPlay',
                         'icon':      self.icon_play,
                         'action':    'Play'},
            'stop':     {'clickable': 'True',
                         'icon':      self.icon_stop,
                         'action':    'Stop'},
            'next':     {'clickable': 'CanGoNext',
                         'icon':      self.icon_next,
                         'action':    'Next'},
            'previous': {'clickable': 'CanGoPrevious',
                         'icon':      self.icon_previous,
                         'action':    'Previous'}
        }

        state = 'pause' if self._player.PlaybackStatus == 'Playing' else 'play'
        control_states['toggle'] = control_states[state]

        return control_states

    def _get_response_buttons(self):
        response = []
        buttons_order = self.buttons_order.split(',')
        available = self._control_states.keys()

        for button in [e for e in buttons_order if e in available]:
            control_state = self._control_states[button]
            clickable = getattr(self._player, control_state['clickable'], True)
            response.append({
                'color': '#CCCCCC' if clickable else '#666666',
                'full_text': control_state['icon'],
                'index': button,
            })

        return response

    def mpris(self, i3s_output_list, i3s_config):
        """
        Get the current output format and return it.
        """
        show_controls = self.show_controls
        cached_until = time() + i3s_config['interval']
        self._dbus = SessionBus()

        running_player = self._detect_running_player()
        self._player = self._get_player(running_player)

        if self._player is None:
            show_controls = None
            text = self.format_none
            color = i3s_config['color_bad']
        else:
            (text, color) = self._get_text(i3s_config)
            self._control_states = self._get_control_states()
            response_buttons = self._get_response_buttons()
            if len(response_buttons) == 0:
                show_controls = None

        response_text = {
            'full_text': text,
            'color': color,
            'index': 'text'
        }

        response = {
            'cached_until': cached_until,
        }

        if show_controls == 'left':
            response['composite'] = response_buttons + [response_text]
        elif show_controls == 'right':
            response['composite'] = [response_text] + response_buttons
        else:
            response['composite'] = [response_text]

        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Handles click events
        """
        index = event['index']
        button = event['button']

        if index == 'text':
            if button == self.button_toggle:
                index = 'toggle'
            elif button == self.button_stop:
                index = 'stop'
            elif button == self.button_next:
                index = 'next'
            elif button == self.button_previous:
                index = 'previous'
        elif button != 1:
            return

        getattr(self._player, self._control_states[index]['action'])()

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
