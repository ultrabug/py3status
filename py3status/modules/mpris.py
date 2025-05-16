"""
Display song/video and control MPRIS compatible players.

There are two ways to control the media player. Either by clicking with a mouse
button in the text information or by using buttons. For former you have
to define the button parameters in your config.

Configuration parameters:
    button_next: mouse button to play the next entry (default None)
    button_next_player: mouse button to switch next player in list (Same status as top player) (default None)
    button_prev_player: mouse button to switch previous player in list (Same status as top player) (default None)
    button_previous: mouse button to play the previous entry (default None)
    button_stop: mouse button to stop the player (default None)
    button_switch_to_top_player: mouse button to switch to top player (default None)
    button_toggle: mouse button to toggle between play and pause mode (default 1)
    cache_timeout: time (s) between Position update (default 0.5)
    format: display format for this module
        (default '[{artist} - ][{title}] {previous} {toggle} {next}')
    format_none: define output if no player is running (default 'no player running')
    icon_next: specify icon for next button (default u'\u25b9')
    icon_pause: specify icon for pause button (default u'\u25eb')
    icon_play: specify icon for play button (default u'\u25b7')
    icon_previous: specify icon for previous button (default u'\u25c3')
    icon_stop: specify icon for stop button (default u'\u25a1')
    max_width: maximum status length (default None)
    player_priority: priority of the players.
        Keep in mind that the state has a higher priority than
        player_priority. So when player_priority is "[mpd, bomi]" and mpd is
        paused and bomi is playing than bomi wins. (default [])
    replacements: specify a list/dict of string placeholders to modify (default None)
    state_pause: specify icon for pause state (default u'\u25eb')
    state_play: specify icon for play state (default u'\u25b7')
    state_stop: specify icon for stop state (default u'\u25a1')

Format placeholders:
    {album} album name
    {artist} artist name (first one)
    {length} time duration of the song
    {player} show name of the player
    {player_shortname} show name of the player from busname (usually command line name)
    {state} playback status of the player
    {time} played time of the song
    {title} name of the song
    {tracknumber} track number of the song
    {nowplaying} now playing field provided by VLC for stream info

Button placeholders:
    {next} play the next title
    {pause} pause the player
    {play} play the player
    {previous} play the previous title
    {stop} stop the player
    {toggle} toggle between play and pause

Color options:
    color_control_inactive: button is not clickable
    color_control_active: button is clickable
    color_paused: song is paused, defaults to color_degraded
    color_playing: song is playing, defaults to color_good
    color_stopped: song is stopped, defaults to color_bad

Requires:
    mpris2: Python usable definiton of MPRIS2
    dbus-python: Python bindings for dbus
    PyGObject: Python bindings for GObject Introspection

Tested players:
    bomi: powerful and easy-to-use gui multimedia player based on mpv
    cantata: qt5 client for the music player daemon (mpd)
    mpdris2: mpris2 support for mpd
    vlc: multi-platform mpeg, vcd/dvd, and divx player

Examples:
```
mpris {
    format = "{previous}{play}{next} {player}: {state} [[{artist} - {title}]|[{title}]]"
    format_none = "no player"
    player_priority = "[mpd, cantata, vlc, bomi, *]"
}

only show information from mpd and vlc, but mpd has a higher priority:
mpris {
    player_priority = "[mpd, vlc]"
}

show information of all players, but mpd and vlc have the highest priority:
mpris {
    player_priority = "[mpd, vlc, *]"
}

vlc has the lowest priority:
mpris {
    player_priority = "[*, vlc]"
}
```

@author Moritz Lüdecke, tobes, valdur55

SAMPLE OUTPUT
[
    {'color': '#00FF00', 'full_text': u'\xab \u25ae \xbb \u25b6 '},
    {'color': '#00FF00', 'full_text': u'Happy Mondays - Fat Lady Wrestlers'}
]
"""

import re
import sys
from datetime import timedelta
from enum import IntEnum
from threading import Thread

from dbus import DBusException, SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from mpris2 import Interfaces
from mpris2 import MediaPlayer2 as dMediaPlayer2
from mpris2 import Player as dPlayer
from mpris2 import get_players_uri
from mpris2.types import Metadata_Map


class STATE(IntEnum):
    Playing = 0
    Paused = 1
    Stopped = 2


# noinspection PyProtectedMember
class Player:
    def __init__(
        self,
        parent,
        player_id,
        name_from_id,
        name_with_instance,
        name_priority,
        identity,
        identity_index,
    ):
        self._id = player_id
        self.parent = parent
        self._name_with_instance = name_with_instance
        self._identity = identity
        self._identity_index = identity_index
        self._name_priority = name_priority
        self._metadata = {}
        self._can = {}
        self._buttons = {}
        self._properties_changed_match = None
        self._state = None
        self._player_shortname = name_from_id
        self._dPlayer = dPlayer(dbus_interface_info={"dbus_uri": player_id})
        self._full_name = f"{self._identity} {self._identity_index}"

        self._placeholders = {
            "player": self._identity,
            "player_shortname": self._player_shortname,
            # for debugging ;p
            "full_name": self._full_name,
        }

        # Init data from dbus interface
        self.state = None
        self.metadata = None

        for canProperty in self.parent._used_can_properties:
            self._set_can_property(canProperty, getattr(self._dPlayer, canProperty))

        # Workaround for bug which prevents to use self._dPlayer.propertiesChanged = handler.
        self._properties_changed_match = self.parent._dbus.add_signal_receiver(
            self._player_on_change,
            dbus_interface=Interfaces.PROPERTIES,
            path=Interfaces.OBJECT_PATH,
            signal_name=Interfaces.SIGNAL,
            bus_name=player_id,
        )

    def __del__(self):
        if self._properties_changed_match:
            self.parent._dbus._clean_up_signal_match(self._properties_changed_match)

    @staticmethod
    def _get_time_str(microseconds):
        if microseconds is None:
            return None

        delta = timedelta(seconds=microseconds // 1_000_000)
        delta_str = str(delta).lstrip("0").lstrip(":")
        if delta_str.startswith("0"):
            delta_str = delta_str[1:]
        return delta_str

    def _set_response_buttons(self):
        buttons = {}

        for button, control_state in self.parent._states.items():
            if self.parent.py3.format_contains(self.parent.format, button):
                if self.get_button_state(control_state):
                    color = self.parent._color_active
                else:
                    color = self.parent._color_inactive

                buttons[button] = {
                    "color": color,
                    "full_text": control_state["icon"],
                    "index": button,
                }

        if buttons.get("toggle"):
            buttons["toggle"]["full_text"] = self.parent._state_icon_color_map[self.state][
                "toggle_icon"
            ]

        self._buttons = buttons

    def _set_can_property(self, key, value):
        self._can[key] = value

    def _player_on_change(self, interface_name, data, invalidated_properties):
        is_active_player = self is self.parent._player
        call_set_player = False
        call_update = False

        for key, new_value in data.items():
            if key == "PlaybackStatus":
                self.state = new_value
                call_set_player = True

            elif key == "Metadata":
                if self.parent._format_contains_metadata:
                    self.metadata = new_value
                    call_update = True

            elif key.startswith("Can"):
                self._set_can_property(key, new_value)
                call_update = True

                if key == "CanPlay":
                    call_set_player = True

            elif key == "Rate":
                if is_active_player:
                    self.state = None
                    call_update = True

        if call_set_player:
            return self.parent._set_player()

        if is_active_player and call_update:
            return self.parent.py3.update()

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata=None):
        if not self.parent._format_contains_metadata:
            return

        if metadata is None:
            metadata = self._dPlayer.Metadata

        self._metadata = {}

        if metadata:
            url = metadata.get(Metadata_Map.URL)
            is_stream = url is not None and "file://" not in url
            if is_stream:
                self._metadata["title"] = re.sub(
                    r"\....$", "", metadata.get(Metadata_Map.TITLE, "")
                )
            else:
                self._metadata["title"] = metadata.get(Metadata_Map.TITLE, None)
            self._metadata["album"] = metadata.get(Metadata_Map.ALBUM, None)

            artist = metadata.get(Metadata_Map.ARTIST, None)
            if artist:
                self._metadata["artist"] = artist[0]

            self._metadata["length"] = self._get_time_str(metadata.get(Metadata_Map.LENGTH))

            # we are converting the attribute name to lowercase because although the spec
            # says it's `xesam:trackNumber`, VLC exposes it as `xesam:tracknumber`
            self._metadata["tracknumber"] = metadata.get(Metadata_Map.TRACK_NUMBER.lower())

            self._metadata["nowplaying"] = metadata.get("vlc:nowplaying", None)

            for x in self.parent.replacements_init:
                if x in self._metadata:
                    self._metadata[x] = self.parent.py3.replace(self._metadata[x], x)

        if not self._metadata.get("title"):
            self._metadata["title"] = "No Track"

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_value):
        if new_value is None:
            new_value = self._dPlayer.PlaybackStatus

        if new_value != self._state:
            self._state = getattr(STATE, new_value)
            if self is self.parent._player:
                self.prepare_output()

    def send_mpris_action(self, index):
        control_state = self.parent._states.get(index)
        try:
            if self.get_button_state(control_state):
                getattr(self._dPlayer, self.parent._states[index]["action"])()
                self.state = None
        except DBusException as err:
            self.parent.py3.log(
                f"Player {self._name_with_instance} responded {str(err).split(':', 1)[-1]}"
            )

    def prepare_output(self):
        if self.parent._format_contains_control_buttons:
            self._set_response_buttons()

    def get_button_state(self, control_state):
        try:
            clickable = self._can.get(control_state["clickable"], True)
        except Exception:
            clickable = False

        if self.state in control_state.get("inactive", []):
            clickable = False

        return clickable

    @property
    def state_map(self):
        return self.parent._state_icon_color_map[self.state]

    @property
    def data(self):
        """
        Output player specific data
        """
        if self.parent._format_contains_time:
            try:
                ptime = self._get_time_str(self._dPlayer.Position)
            except DBusException:
                ptime = None

            self._placeholders["time"] = ptime

        return dict(self._placeholders, **self.metadata, **self._buttons)

    @property
    def hide(self):
        return not self._can.get("CanPlay")

    @property
    def id(self):
        return self._id

    @property
    def priority_tuple(self):
        if self.hide:
            return None

        return self._state, self._name_priority, self._identity_index, self.id


class Py3status:
    """ """

    # available configuration parameters
    button_next = None
    button_next_player = None
    button_prev_player = None
    button_previous = None
    button_stop = None
    button_switch_to_top_player = None
    button_toggle = 1
    cache_timeout = 0.5
    format = "[{artist} - ][{title}] {previous} {toggle} {next}"
    format_none = "no player running"
    icon_next = "\u25b9"
    icon_pause = "\u25eb"
    icon_play = "\u25b7"
    icon_previous = "\u25c3"
    icon_stop = "\u25a1"
    max_width = None
    player_priority = []
    replacements = None
    state_pause = "\u25eb"
    state_play = "\u25b7"
    state_stop = "\u25a1"

    class Meta:
        deprecated = {
            'remove': [
                {
                    'param': 'player_hide_non_canplay',
                    'msg': 'obsolete because we now hide all non canplay players',
                },
            ],
        }

    def post_config_hook(self):
        self.replacements_init = self.py3.get_replacements_list(self.format)
        self._name_owner_change_match = None
        self._kill = False
        self._mpris_players: dict[Player] = {}
        self._identity_cache = {}
        self._identity_index = {}
        self._priority_cache = {}
        self._player: [Player, None] = None
        self._tries = 0
        self._empty_response = {
            "album": None,
            "artist": None,
            "length": None,
            "title": None,
            "tracknumber": None,
            "nowplaying": None,
            "time": None,
            "state": None,
            "player": None,
            # for debugging ;p
            "full_name": None,
        }

        self._states = {
            "pause": {
                "action": "Pause",
                "clickable": "CanPause",
                "icon": self.icon_pause,
                "inactive": [STATE.Stopped, STATE.Paused],
            },
            "play": {
                "action": "Play",
                "clickable": "CanPlay",
                "icon": self.icon_play,
                "inactive": [STATE.Playing],
            },
            "stop": {
                "action": "Stop",
                "clickable": "CanControl",
                "icon": self.icon_stop,
                "inactive": [STATE.Stopped],
            },
            "next": {
                "action": "Next",
                "clickable": "CanGoNext",
                "icon": self.icon_next,
            },
            "previous": {
                "action": "Previous",
                "clickable": "CanGoPrevious",
                "icon": self.icon_previous,
            },
            "toggle": {
                "action": "PlayPause",
                "clickable": "CanPause",
                # Not used, but it will be set dynamically with player state map.
                "icon": None,
            },
        }

        self._state_icon_color_map = {
            STATE.Playing: {
                "state_icon": self.state_play,
                "color": self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD,
                "toggle_icon": self.state_pause,
                "cached_until": self.cache_timeout,
            },
            STATE.Paused: {
                "state_icon": self.state_pause,
                "color": self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED,
                "toggle_icon": self.state_play,
                "cached_until": self.py3.CACHE_FOREVER,
            },
            STATE.Stopped: {
                "state_icon": self.state_stop,
                "color": self.py3.COLOR_STOPPED or self.py3.COLOR_BAD,
                "toggle_icon": self.state_play,
                "cached_until": self.py3.CACHE_FOREVER,
            },
        }

        self._color_active = self.py3.COLOR_CONTROL_ACTIVE or self.py3.COLOR_GOOD
        self._color_inactive = self.py3.COLOR_CONTROL_INACTIVE or self.py3.COLOR_BAD

        self._format_contains_metadata = False
        self._metadata_keys = ["album", "artist", "title", "nowplaying", "length", "tracknumber"]
        for key in self._metadata_keys:
            if self.py3.format_contains(self.format, key):
                self._format_contains_metadata = True
                break

        self._format_contains_control_buttons = False
        self._used_can_properties = []
        for key, value in self._states.items():
            if self.py3.format_contains(self.format, key):
                self._format_contains_control_buttons = True
                self._used_can_properties.append(value["clickable"])

        if "CanPlay" not in self._used_can_properties:
            self._used_can_properties.append("CanPlay")

        self._format_contains_time = self.py3.format_contains(self.format, "time")
        self._button_cache_flush = None
        if 2 not in [
            self.button_next,
            self.button_next_player,
            self.button_prev_player,
            self.button_previous,
            self.button_stop,
            self.button_switch_to_top_player,
            self.button_toggle,
        ]:
            self._button_cache_flush = 2

        if self.player_priority:
            try:
                self._random_player_priority = self.player_priority.index("*")
            except ValueError:
                self._random_player_priority = False
        else:
            self._random_player_priority = 0

        # start last
        self._dbus_loop = DBusGMainLoop()
        self._dbus = SessionBus(mainloop=self._dbus_loop)
        self._start_listener()

    def _start_loop(self):
        self._loop = GLib.MainLoop()
        GLib.timeout_add(1000, self._timeout)
        try:
            self._loop.run()
        except KeyboardInterrupt:
            # This branch is only needed for the test mode
            self._kill = True

    @staticmethod
    def _is_mediaplayer_interface(player_id):
        return player_id.startswith(Interfaces.MEDIA_PLAYER)

    def _dbus_name_owner_changed(self, name, old_owner, new_owner):
        if not self._is_mediaplayer_interface(name):
            return
        if new_owner:
            self._add_player(name)
        if old_owner:
            self._remove_player(name)
        self._set_player()

    def _set_player(self, update=True):
        """
        Sort the current players into priority order and set self._player
        Players are ordered by working state, then by preference supplied by
        user and finally by instance if a player has more than one running.
        """
        players = []
        for name, player in self._mpris_players.items():
            player_priority_tuple = player.priority_tuple
            if player_priority_tuple:
                players.append(player_priority_tuple)

        new_top_player_id = None
        if players:
            new_top_player_id = sorted(players)[0][3]

        self._set_data_entry_point_by_name_key(new_top_player_id, update)

    def _player_on_change(self, interface_name, data, invalidated_properties, sender):
        """
        Monitor a player and update its status.
        """
        pass

    def _add_player(self, player_id):
        """
        Add player to mpris_players
        """
        player_id_parts_list = player_id.split(".")
        name_from_id = player_id_parts_list[3]

        identity = None
        if name_from_id not in ["chromium", "kdeconnect"]:
            identity = self._identity_cache.get(name_from_id)

        if not identity:
            dMediaPlayer = dMediaPlayer2(dbus_interface_info={"dbus_uri": player_id})
            identity = str(dMediaPlayer.Identity)
            self._identity_cache[name_from_id] = identity

        if self.player_priority:
            # Expected value: numeric / False, None is cache miss.
            priority = self._priority_cache.get(name_from_id, None)
            if priority is None:
                for i, _player in enumerate(self.player_priority):
                    if _player == name_from_id or _player == identity:
                        priority = i
                        break

                if priority is None:
                    priority = self._random_player_priority
                self._priority_cache[identity] = priority

            if not isinstance(priority, int):
                return

        else:
            priority = 0

        identity_index = self._identity_index.get(identity, 0)
        if identity_index:
            self._identity_index[identity] += 1
        else:
            self._identity_index[identity] = 1

        name_with_instance = ".".join(player_id_parts_list[3:])

        player = Player(
            self,
            player_id=player_id,
            name_from_id=name_from_id,
            name_with_instance=name_with_instance,
            name_priority=priority,
            identity=identity,
            identity_index=identity_index,
        )

        self._mpris_players[player_id] = player

    def _remove_player(self, player_id):
        """
        Remove player from mpris_players
        """
        if self._mpris_players.get(player_id):
            del self._mpris_players[player_id]

    def _get_players(self):
        for player in get_players_uri():
            try:
                # str(player) helps avoid to use dbus.Str(*) as dict key
                self._add_player(str(player))
            except DBusException:
                continue

        self._set_player()

    def _start_listener(self):
        self._get_players()

        self._name_owner_change_match = self._dbus.add_signal_receiver(
            handler_function=self._dbus_name_owner_changed,
            dbus_interface="org.freedesktop.DBus",
            signal_name="NameOwnerChanged",
        )

        # Start listening things after initiating players.
        t = Thread(target=self._start_loop)
        t.daemon = True
        t.start()

    def _timeout(self):
        if self._kill:
            self._loop.quit()
            sys.exit(0)

    def _set_data_entry_point_by_name_key(self, new_active_player_key, update=True):
        if self._player is None or new_active_player_key != self._player.id:
            self._player = self._mpris_players.get(new_active_player_key, None)
            if self._player:
                self._player.prepare_output()

        if update:
            self.py3.update()

    def kill(self):
        self._kill = True
        if self._name_owner_change_match:
            self._dbus._clean_up_signal_match(self._name_owner_change_match)

    def mpris(self):
        """
        Get the current output format and return it.
        """
        if self._kill:
            raise KeyboardInterrupt

        current_player = self._player
        cached_until = self.py3.CACHE_FOREVER
        color = self.py3.COLOR_BAD

        if current_player:
            current_player_id = str(current_player.id)
            current_state_map = current_player.state_map
            data = current_player.data

            if current_player_id == self._player.id:
                if self._format_contains_time:
                    cached_until = self.py3.time_in(
                        seconds=current_state_map.get("cached_until"), sync_to=0
                    )

                placeholders = {"state": current_state_map["state_icon"]}
                color = current_state_map["color"]
                composite = self.py3.safe_format(
                    self.format,
                    dict(self._empty_response, **placeholders, **data),
                    max_width=self.max_width,
                )
            else:
                # The player changed during our processing
                # This is usually due to something like a player being killed
                # whilst we are checking its details
                # Retry but limit the number of attempts
                self._tries += 1
                if self._tries < 3:
                    return self.mpris()

                # Max retries hit we need to output something
                return {
                    # Can't decide what is good time to restart 3 retry cycle
                    "cached_until": self.py3.time_in(10),
                    "color": self.py3.COLOR_BAD,
                    "composite": [
                        {
                            "full_text": "Something went wrong",
                            "color": self.py3.COLOR_BAD,
                        }
                    ],
                }

        else:
            composite = [{"full_text": self.format_none, "color": color}]

        # we are outputting so reset tries
        self._tries = 0

        response = {
            "cached_until": cached_until,
            "color": color,
            "composite": composite,
        }
        return response

    def on_click(self, event):
        """
        Handles click events
        """
        index = event["index"]
        button = event["button"]

        if not self._player:
            return

        if button == self._button_cache_flush:
            self._player.metadata = None
            self._player.state = None

        elif index not in self._states:
            if button == self.button_toggle:
                return self._player.send_mpris_action("toggle")
            elif button == self.button_stop:
                return self._player.send_mpris_action("stop")
            elif button == self.button_next:
                return self._player.send_mpris_action("next")
            elif button == self.button_previous:
                return self._player.send_mpris_action("previous")
            elif button == self.button_switch_to_top_player:
                return self._set_player(update=False)

            elif button == self.button_prev_player or button == self.button_next_player:
                switchable_players = []
                order_asc = button == self.button_next_player
                current_player_index = False
                for key, player in self._mpris_players.items():
                    if player.state == self._player.state and not player.hide:
                        if not current_player_index:
                            if player.id == self._player.id:
                                current_player_index = len(switchable_players)
                                if order_asc:
                                    continue

                        switchable_players.append(key)
                        if current_player_index:
                            if order_asc:
                                break
                            else:
                                if current_player_index != 0:
                                    break

                if len(switchable_players):
                    try:
                        if order_asc:
                            next_index = current_player_index % len(switchable_players)
                        else:
                            next_index = (current_player_index - 1) % len(switchable_players)

                        self._set_data_entry_point_by_name_key(
                            switchable_players[next_index], update=False
                        )

                    except KeyError:
                        pass

            else:
                return

        elif button == 1:
            self._player.send_mpris_action(index)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
