# -*- coding: utf-8 -*-
"""
Display information about the current song and video playing on player with
mpris support.

There are two ways to control the media player. Either by clicking with a mouse
button in the text information or by using buttons. For former you have
to define the button parameters in the i3status config.

Configuration parameters:
    button_stop: mouse button to stop the player (default None)
    button_toggle: mouse button to toggle between play and pause mode (default 1)
    button_next: mouse button to play the next entry (default 4)
    button_previous: mouse button to play the previous entry (default 5)
    color_control_inactive: button color if button is not clickable
    color_control_active: button color if button is clickable
    color_paused: text color when song is paused, defaults to color_degraded
    color_playing: text color when song is playing, defaults to color_good
    color_stopped: text color when song is stopped, defaults to color_bad
    format: see placeholders below
    format_none: define output if no player is running
    icon_pause: text for the pause button in the button control panel (default '▮')
    icon_play: text for the play button in the button control panel (default '▶')
    icon_stop: text for the stop button in the button control panel (default '◾')
    icon_next: text for the next button in the button control panel (default '»')
    icon_previous: text for the previous button in the button control panel (default '«')
    state_pause: text for placeholder {state} when song is paused (default '▮')
    state_play: text for placeholder {state} when song is playing (default '▶')
    state_stop: text for placeholder {state} when song is stopped (default '◾')
    player_priority: priority of the players. (default [])
            Keep in mind that the state has a higher priority than
            player_priority. So when player_priority is "[mpd, bomi]" and mpd is
            paused and bomi is playing than bomi wins.

Format of status string placeholders:
    {album} album name
    {artist} artiste name (first one)
    {length} time duration of the song
    {player} show name of the player
    {state} playback status of the player
    {time} played time of the song
    {title} name of the song

Format of button placeholders:
    {next} play the next title
    {pause} pause the player
    {play} play the player
    {previous} play the previous title
    {stop} stop the player
    {toggle} toggle between play and pause

i3status.conf example:

```
mpris {
    format = "{previous}{play}{next} {player}: {state} [[{artist} - {title}]|[{title}]]"
    format_none = "no player"
    player_priority = "[mpd, cantata, vlc, bomi, *]"
}
```

only show information from mpd and vlc, but mpd has a higher priority:

```
mpris {
    player_priority = "[mpd, vlc]"
}
```

show information of all players, but mpd and vlc have the highest priority:

```
mpris {
    player_priority = "[mpd, vlc, *]"
}
```

vlc has the lowest priority:

```
mpris {
    player_priority = "[*, vlc]"
}
```

Requires:
    pydbus

Tested players:
    bomi
    Cantata
    mpDris2 (mpris extension for mpd)
    vlc

@author Moritz Lüdecke, tobes
"""

from datetime import timedelta
from time import time
from gi.repository import GObject
from threading import Thread
import re
from pydbus import SessionBus


SERVICE_BUS = 'org.mpris.MediaPlayer2'
INTERFACE = SERVICE_BUS + '.Player'
SERVICE_BUS_URL = '/org/mpris/MediaPlayer2'
SERVICE_BUS_REGEX = '^' + re.sub(r'\.', '\.', SERVICE_BUS) + '.'

PLAYING = 0
PAUSED = 1
STOPPED = 2


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
    color_control_inactive = None
    color_control_active = None
    color_paused = None
    color_playing = None
    color_stopped = None
    format = '{previous}{toggle}{next} {state}[ [{artist} - {title}]| {title}]'
    format_none = 'no player running'
    icon_pause = u'▮'
    icon_play = u'▶'
    icon_stop = u'◾'
    icon_next = u'»'
    icon_previous = u'«'
    state_pause = u'▮'
    state_play = u'▶'
    state_stop = u'◾'
    player_priority = []

    def __init__(self):
        self._dbus = None
        self._player = None
        self._player_name = 'None'
        self._player_subscription = None

    def _init_data(self):
        self._data = {
            'album': None,
            'artist': None,
            'error_occurred': False,
            'length': None,
            'player': None,
            'state': STOPPED,
            'title': None
        }

        if self._player is None:
            return

        try:
            self._data['player'] = self._player.Identity
            self._data['state'] = self._get_state()
            self._update_metadata()
        except Exception:
            self._data['error_occurred'] = True

    def _on_available_players_changed(self, *args):
        if len(args) < 6:
            return
        if args[5][0].startswith('org.mpris.MediaPlayer2'):
            self.py3.update()

    def _on_change(self, bus, data, nop):
        self._data['error_occurred'] = False

        for field in data:
            if field == 'Metadata':
                self._update_metadata(data[field])
            elif field == 'PlaybackStatus':
                self._data['state'] = self._get_state(state=data[field])

        self.py3.update()

    def _get_button_state(self, control_state):
        clickable = getattr(self._player, control_state['clickable'], True)

        if control_state['action'] == 'Play' and self._data['state'] == PLAYING:
            clickable = False
        elif control_state['action'] == 'Pause' and (
             self._data['state'] == STOPPED or self._data['state'] == PAUSED):
            clickable = False
        elif control_state['action'] == 'Stop' and self._data['state'] == STOPPED:
            clickable = False

        return clickable

    def _get_highest_prioritized(self):
        """
        Detect running player process, if any
        """
        players_paused = []
        players_stopped = []
        players = []
        players_prioritized = []

        dbus = self._dbus.get('org.freedesktop.DBus')
        for player in dbus.ListNames():
            if SERVICE_BUS in player:
                player = re.sub(r'%s' % SERVICE_BUS_REGEX, '', player)
                players.append(player)

        if len(self.player_priority) == 0:
            players_prioritized = players
        else:
            wildcard = []
            lowest = []
            for player_name in self.player_priority:
                if player_name is '*':
                    wildcard = players
                elif player_name in players:
                    players.remove(player_name)
                    if len(wildcard) > 0:
                        if player_name in wildcard:
                            wildcard.remove(player_name)
                        lowest.append(player_name)
                    else:
                        players_prioritized.append(player_name)
            players_prioritized = players_prioritized + wildcard + lowest

        for player_name in players_prioritized:
            player = self._get_player(player_name)
            if player is None:
                continue
            player_state = self._get_state(player)

            if player_state == PLAYING:
                return player_name
            elif player_state == PAUSED:
                players_paused.append(player_name)
            else:
                players_stopped.append(player_name)

        if players_paused:
            return players_paused[0]
        if players_stopped:
            return players_stopped[0]

        return 'None'

    def _get_player(self, player):
        """
        Get dbus object
        """
        try:
            return self._dbus.get(SERVICE_BUS + '.%s' % player, SERVICE_BUS_URL)
        except Exception:
            return None

    def _get_state(self, player=None, state=None):
        if state:
            playback_status = state
        elif player:
            playback_status = player.PlaybackStatus
        else:
            playback_status = self._player.PlaybackStatus

        if playback_status == 'Playing':
            return PLAYING
        elif playback_status == 'Paused':
            return PAUSED
        else:
            return STOPPED

    def _get_text(self, i3s_config):
        """
        Get the current metadata
        """
        if self._data['state'] == PLAYING:
            color = self.color_playing or i3s_config['color_good']
            state_symbol = self.state_play
        elif self._data['state'] == PAUSED:
            color = self.color_paused or i3s_config['color_degraded']
            state_symbol = self.state_pause
        else:
            color = self.color_stopped or i3s_config['color_bad']
            state_symbol = self.state_stop

        if self._data['error_occurred']:
            color = i3s_config['color_bad']

        try:
            ptime_ms = self._player.Position
            ptime = _get_time_str(ptime_ms)
        except Exception:
            ptime = None

        if '{time}' in self.format and self._data['state'] == PLAYING:
            # Don't get trapped in aliasing errors!
            update = time() + 0.5
        else:
            update = self.py3.CACHE_FOREVER

        placeholders = {
            'player': self._data['player'],
            'state': state_symbol,
            'album': self._data['album'],
            'artist': self._data['artist'],
            'length': self._data['length'],
            'time': ptime,
            'title': self._data['title']
        }

        return (placeholders, color, update)

    def _get_control_states(self):
        control_states = {
            'pause':    {'action':    'Pause',
                         'clickable': 'CanPause',
                         'icon':      self.icon_pause},
            'play':     {'action':    'Play',
                         'clickable': 'CanPlay',
                         'icon':      self.icon_play},
            'stop':     {'action':    'Stop',
                         'clickable': 'True',
                         'icon':      self.icon_stop},
            'next':     {'action':    'Next',
                         'clickable': 'CanGoNext',
                         'icon':      self.icon_next},
            'previous': {'action':    'Previous',
                         'clickable': 'CanGoPrevious',
                         'icon':      self.icon_previous}
        }

        state = 'pause' if self._data['state'] == PLAYING else 'play'
        control_states['toggle'] = control_states[state]

        return control_states

    def _get_response_buttons(self, i3s_config):
        response = {}

        for button in self._control_states.keys():
            control_state = self._control_states[button]

            if self._get_button_state(control_state):
                color = self.color_control_active or i3s_config['color_good']
            else:
                color = self.color_control_inactive or i3s_config['color_bad']

            response[button] = {
                'color': color,
                'full_text': control_state['icon'],
                'index': button,
                'min_width': 20,
                'align': 'center'
            }

        return response

    def _start_loop(self):
        self._loop = GObject.MainLoop()
        self._loop.run()

    def _start_listener(self):
        self._dbus.con.signal_subscribe(
            None,
            'org.freedesktop.DBus',
            'NameOwnerChanged',
            None,
            None,
            0,
            self._on_available_players_changed,
        )
        t = Thread(target=self._start_loop)
        t.daemon = True
        t.start()

    def _update_metadata(self, metadata=None):
        is_stream = False

        if metadata is None:
            metadata = self._player.Metadata

        try:
            if len(metadata) > 0:
                url = metadata.get('xesam:url')
                is_stream = url is not None and 'file://' not in url
                self._data['title'] = metadata.get('xesam:title')
                self._data['album'] = metadata.get('xesam:album')

                if metadata.get('xesam:artist') is not None:
                    self._data['artist'] = metadata.get('xesam:artist')[0]
                else:
                    # we assume here that we playing a video and these types of
                    # media we handle just like streams
                    is_stream = True

                length_ms = metadata.get('mpris:length')
                if length_ms is not None:
                    self._data['length'] = _get_time_str(length_ms)
            else:
                # use stream format if no metadata is available
                is_stream = True
        except Exception:
            self._data['error_occurred'] = True

        if is_stream and self._data['title']:
            # delete the file extension
            self._data['title'] = re.sub(r'\....$', '', self._data['title'])

    def mpris(self, i3s_output_list, i3s_config):
        """
        Get the current output format and return it.
        """
        cached_until = self.py3.CACHE_FOREVER

        if self._dbus is None:
            self._dbus = SessionBus()
            self._start_listener()

        running_player = self._get_highest_prioritized()
        if self._player is None or self._player_name != running_player:
            if self._player_subscription:
                self._player_subscription.disconnect()
            self._player_name = running_player
            self._player = self._get_player(running_player)
            self._init_data()
            if self._player is not None:
                self._player_subscription = self._player.PropertiesChanged.connect(self._on_change)

        if self._player is None:
            self._player = None
            self._player_name = 'None'
            self._player_subscription = None
            text = self.format_none
            color = i3s_config['color_bad']
            composite = [{
                'full_text': text,
                'color': color,
            }]
        else:
            (text, color, cached_until) = self._get_text(i3s_config)
            self._control_states = self._get_control_states()
            buttons = self._get_response_buttons(i3s_config)
            composite = self.py3.build_composite(self.format,
                                                 text,
                                                 buttons)

        response = {
            'cached_until': cached_until,
            'color': color,
            'composite': composite
        }

        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Handles click events
        """
        index = event['index']
        button = event['button']

        if index not in self._control_states.keys():
            if button == self.button_toggle:
                index = 'toggle'
            elif button == self.button_stop:
                index = 'stop'
            elif button == self.button_next:
                index = 'next'
            elif button == self.button_previous:
                index = 'previous'
            else:
                return
        elif button != 1:
            return

        control_state = self._control_states[index]
        if self._player and self._get_button_state(control_state):
            getattr(self._player, self._control_states[index]['action'])()

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
