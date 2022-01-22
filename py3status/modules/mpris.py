"""
Display song/video and control MPRIS compatible players.

There are two ways to control the media player. Either by clicking with a mouse
button in the text information or by using buttons. For former you have
to define the button parameters in your config.

Configuration parameters:
    button_next: mouse button to play the next entry (default None)
    button_next_player: (Experimental) mouse button to switch next player in list (Same status as top player) (default None)
    button_prev_player: (Experimental) mouse button to switch previous player in list (Same status as top player) (default None)
    button_previous: mouse button to play the previous entry (default None)
    button_stop: mouse button to stop the player (default None)
    button_switch_to_top_player: (Experimental) mouse button to switch to toop player (default None)
    button_toggle: mouse button to toggle between play and pause mode (default 1)
    format: see placeholders below
    format: display format for this module
        (default '[{artist} - ][{title}] {previous} {toggle} {next}')
    format_none: define output if no player is running (default 'no player running')
    icon_next: specify icon for next button (default u'\u25b9')
    icon_pause: specify icon for pause button (default u'\u25eb')
    icon_play: specify icon for play button (default u'\u25b7')
    icon_previous: specify icon for previous button (default u'\u25c3')
    icon_stop: specify icon for stop button (default u'\u25a1')
    player_hide_non_canplay: Used to hide chrome/chomium players on idle state. (default ['chrome', 'chromium'])
    player_priority: priority of the players.
        Keep in mind that the state has a higher priority than
        player_priority. So when player_priority is "[mpd, bomi]" and mpd is
        paused and bomi is playing than bomi wins. (default [])
    state_pause: specify icon for pause state (default u'\u25eb')
    state_play: specify icon for play state (default u'\u25b7')
    state_stop: specify icon for stop state (default u'\u25a1')

Format placeholders:
    {album} album name
    {artist} artiste name (first one)
    {length} time duration of the song
    {player} show name of the player
    {state} playback status of the player
    {time} played time of the song
    {title} name of the song
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
    dbus: Python bindings for dbus

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
from datetime import timedelta
import time
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject
from threading import Thread
import re
import sys
from dbus import SessionBus, DBusException
from mpris2 import Player as dPlayer, MediaPlayer2 as dMediaPlayer2
from mpris2 import get_players_uri, Interfaces
from mpris2.types import Metadata_Map
from enum import IntEnum

STRING_GEVENT = "this module does not work with gevent"
ALWAYS_CLICKABLE = "always"


class STATE(IntEnum):
    Playing = 0
    Paused = 1
    Stopped = 2


def _get_time_str(microseconds):
    delta = timedelta(seconds=microseconds // 1_000_000)
    delta_str = str(delta).lstrip("0").lstrip(":")
    if delta_str.startswith("0"):
        delta_str = delta_str[1:]
    return delta_str


# noinspection PyProtectedMember
class Player:
    def __init__(self, parent, player_id, name_from_id, name_with_instance):
        self.id = player_id
        self.parent = parent
        self.name_with_instance = name_with_instance
        self._states = parent._states
        self._name = name_from_id
        self._dbus = dPlayer(dbus_interface_info={"dbus_uri": player_id})
        self._metadata = {}
        self._can = {}
        self._buttons = {}
        self._state = None
        self.player_name, self._index = self.parent._get_mpris_name(self)
        self.full_name = f"{name_with_instance} {self._index}"
        self._name_in_player_hide_non_canplay = (
            self._name in self.parent.player_hide_non_canplay
        )
        self.state = None
        self.metadata = None
        self._set_priority()

        for canProperty in self.parent._used_can_properties:
            self._can[canProperty] = getattr(self._dbus, canProperty)

        self._placeholders = {
            "player": self.player_name,
            # for debugging ;p
            "full_name": self.full_name,
        }

    @property
    def hide(self):
        return self._name_in_player_hide_non_canplay and not self._can.get("CanPlay")

    @property
    def can(self):
        return self._can

    @property
    def buttons(self):
        return self._buttons

    def _set_priority(self):
        if self.parent.player_priority:
            try:
                priority = self.parent.player_priority.index(self._name)
            except ValueError:
                try:
                    priority = self.parent.player_priority.index("*")
                except ValueError:
                    priority = 0
        else:
            priority = 0

        self._priority = priority

    @property
    def priority_tuple(self):
        if self.hide:
            return None

        return self._state, self._priority, self._index, self.id

    @property
    def metadata(self):
        return self._metadata

    def set_can_property(self, key, value):
        self._can[key] = value

    @property
    def name(self):
        return self._name

    @metadata.setter
    def metadata(self, metadata=None):
        if not self.parent._format_contains_metadata:
            self._metadata = {}
            return

        if metadata is None:
            metadata = self._dbus.Metadata

        is_stream = False

        try:
            if len(metadata) > 0:
                url = metadata.get(Metadata_Map.URL)
                is_stream = url is not None and "file://" not in url
                self._metadata["title"] = metadata.get(Metadata_Map.TITLE, None)
                self._metadata["album"] = metadata.get(Metadata_Map.ALBUM, None)

                artist = metadata.get(Metadata_Map.ARTIST, None)
                if len(artist):
                    self._metadata["artist"] = artist[0] or None
                else:
                    # we assume here that we playing a video and these types of
                    # media we handle just like streams
                    is_stream = True

                length_ms = metadata.get(Metadata_Map.LENGTH)
                if length_ms:
                    self._metadata["length"] = _get_time_str(length_ms)
                else:
                    self._metadata["length"] = None
            else:
                # use stream format if no metadata is available
                is_stream = True
        except Exception:
            self._metadata["error_occurred"] = True

        if is_stream and self._metadata.get("title"):
            # delete the file extension
            self._metadata["title"] = re.sub(r"\....$", "", self._metadata.get("title"))
            self._metadata["nowplaying"] = metadata.get("vlc:nowplaying", None)

        if not self._metadata.get("title"):
            self._metadata["title"] = "No Track"

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_value):
        if new_value is None:
            new_value = self._dbus.PlaybackStatus

        if new_value != self._state:
            self._state = getattr(STATE, new_value)
            if self.parent._player == self:
                self.prepare_output()

    def send_mpris_action(self, index):
        control_state = self.self._states.get(index)
        try:
            if self.get_button_state(control_state):
                getattr(self._dbus, self.self._states[index]["action"])()
                self.state = None
        except DBusException as err:
            self.parent.py3.log(
                f"Player {self._name} responded {str(err).split(':', 1)[-1]}"
            )

    def prepare_output(self):
        if self.parent._format_contains_control_buttons:
            self._set_response_buttons()

    def get_button_state(self, control_state):
        # Toggle and Stop are always clickable
        if control_state["clickable"] == ALWAYS_CLICKABLE:
            return True

        try:
            clickable = getattr(self.can, control_state["clickable"], True)
        except Exception:
            clickable = False

        if control_state["action"] == "Play" and self.state == STATE.Playing:
            clickable = False
        elif control_state["action"] == "Pause" and self.state in [
            STATE.Stopped,
            STATE.Paused,
        ]:
            clickable = False
        elif control_state["action"] == "Stop" and self.state == STATE.Stopped:
            clickable = False

        return clickable

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

        self._buttons = buttons

    def get_text(self):
        """
        Get the current metadata
        """
        ptime = None
        cache_until = self.parent.py3.CACHE_FOREVER

        if self.parent._format_contains_time:
            try:
                ptime_ms = getattr(self._dbus, "Position", None)
            except DBusException:
                ptime_ms = None

            if ptime_ms is not None:
                ptime = _get_time_str(ptime_ms)
                if self.state == STATE.Playing:
                    cache_until = time.perf_counter() + 0.5

        placeholders = {
            "time": ptime,
        }

        return (
            dict(self._placeholders, **placeholders, **self.metadata, **self.buttons),
            cache_until,
        )


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
    format = "[{artist} - ][{title}] {previous} {toggle} {next}"
    format_none = "no player running"
    icon_next = "\u25b9"
    icon_pause = "\u25eb"
    icon_play = "\u25b7"
    icon_previous = "\u25c3"
    icon_stop = "\u25a1"
    player_hide_non_canplay = ["chrome", "chromium"]
    player_priority = []
    state_pause = "\u25eb"
    state_play = "\u25b7"
    state_stop = "\u25a1"

    def post_config_hook(self):
        # TODO: Look again if it is needed
        if self.py3.is_gevent():
            raise Exception(STRING_GEVENT)
        self._data = {}
        self._control_states = {}
        self._ownerToPlayerId = {}
        self._kill = False
        self._mpris_players: dict[Player] = {}
        self._mpris_names = {}
        self._mpris_name_index = {}
        self._player: [Player, None] = None
        self._tries = 0
        self._empty_response = {
            "album": None,
            "artist": None,
            "length": None,
            "title": None,
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
            },
            "play": {"action": "Play", "clickable": "CanPlay", "icon": self.icon_play},
            "stop": {
                "action": "Stop",
                "clickable": ALWAYS_CLICKABLE,  # The MPRIS API lacks 'CanStop' function.
                "icon": self.icon_stop,
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
                # By mpris spec it recommends CanPause check, but works well withoit it
                "clickable": ALWAYS_CLICKABLE,
                "icon": None,
            },
        }

        self._state_icon_color_map = {
            STATE.Playing: {
                "state_icon": self.state_play,
                "color": self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD,
                "toggle_icon": self.state_pause,
            },
            STATE.Paused: {
                "state_icon": self.state_pause,
                "color": self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED,
                "toggle_icon": self.state_play,
            },
            STATE.Stopped: {
                "state_icon": self.state_stop,
                "color": self.py3.COLOR_STOPPED or self.py3.COLOR_BAD,
                "toggle_icon": self.state_play,
            },
        }

        self._color_active = self.py3.COLOR_CONTROL_ACTIVE or self.py3.COLOR_GOOD
        self._color_inactive = self.py3.COLOR_CONTROL_INACTIVE or self.py3.COLOR_BAD

        self._format_contains_metadata = False
        self._metadata_keys = ["album", "artist", "title", "nowplaying"]
        for key in self._metadata_keys:
            if self.py3.format_contains(self.format, key):
                self._format_contains_metadata = True
                break

        self._format_contains_control_buttons = False
        self._used_can_properties = []
        for key, value in self._states.items():
            if value["clickable"] != ALWAYS_CLICKABLE and self.py3.format_contains(
                self.format, key
            ):
                self._format_contains_control_buttons = True
                self._used_can_properties.append(value["clickable"])

        if (
            len(self.player_hide_non_canplay)
            and "CanPlay" not in self._used_can_properties
        ):
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

        # start last
        self._dbus_loop = DBusGMainLoop()
        self._dbus = SessionBus(mainloop=self._dbus_loop)
        self._start_listener()

    def _get_mpris_name(self, player):
        name = self._mpris_names.get(player.id)
        if not name:
            dMediaPlayer = dMediaPlayer2(dbus_interface_info={"dbus_uri": player.id})
            name = str(dMediaPlayer.Identity)
            self._mpris_names[player.name] = name

        if player.name not in self._mpris_name_index:
            self._mpris_name_index[player.name] = 0

        index = self._mpris_name_index[player.name]
        self._mpris_name_index[player.name] += 1

        return (name, index)

    def _start_loop(self):
        self._loop = GObject.MainLoop()
        GObject.timeout_add(1000, self._timeout)
        try:
            self._loop.run()
        except KeyboardInterrupt:
            # This branch is only needed for the test mode
            self._kill = True

    def _is_mediaplayer_interface(self, player_id):
        return player_id.startswith(Interfaces.MEDIA_PLAYER)

    def _dbus_name_owner_changed(self, name, old_owner, new_owner):
        if not self._is_mediaplayer_interface(name):
            return
        if new_owner:
            self._add_player(name, new_owner)
        if old_owner:
            self._remove_player(name, old_owner)
        self._set_player()

    def _set_player(self, update=True):
        """
        Sort the current players into priority order and set self._player
        Players are ordered by working state, then by preference supplied by
        user and finally by instance if a player has more than one running.
        """
        players = []
        for name, player in self._mpris_players.items():
            # we set the priority here as we need to establish the player name
            # which might not be immediately available.
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
        sender_player_id = self._ownerToPlayerId.get(sender)
        if not sender_player_id:
            return
        sender_player: [Player, None] = self._mpris_players.get(sender_player_id)
        if not sender_player:
            return
        sender_is_active_player = sender_player_id == self._player.id

        call_set_player = False
        call_update = False

        for key, new_value in data.items():

            if key == "PlaybackStatus":
                sender_player.state = new_value
                call_set_player = True

            elif key == "Metadata":
                if self._format_contains_metadata:
                    sender_player.metadata = new_value
                    call_update = True

            elif key.startswith("Can"):
                sender_player.set_can_property(key, new_value)
                call_update = True

                if key == "CanPlay":
                    call_set_player = True

            elif key == "Rate":
                if sender_is_active_player:
                    sender_player.state = None
                    call_update = True

        if call_set_player:
            return self._set_player()

        if sender_is_active_player and call_update:
            return self.py3.update()

    def _add_player(self, player_id, owner):
        """
        Add player to mpris_players
        """
        player_id_parts_list = player_id.split(".")
        name_from_id = player_id_parts_list[3]

        if (
            self.player_priority != []
            and name_from_id not in self.player_priority
            and "*" not in self.player_priority
        ):
            return False

        name_with_instance = ".".join(player_id_parts_list[3:])

        player = Player(self, player_id, name_from_id, name_with_instance)

        self._mpris_players[player_id] = player
        self._ownerToPlayerId[owner] = player_id

    def _remove_player(self, player_id, owner):
        """
        Remove player from mpris_players
        """
        if self._ownerToPlayerId.get(owner):
            del self._ownerToPlayerId[owner]

        if self._mpris_players.get(player_id):
            del self._mpris_players[player_id]

    def _get_players(self):
        for player in get_players_uri():
            try:
                # str(player) helps avoid to use dbus.Str(*) as dict key
                self._add_player(str(player), self._dbus.get_name_owner(player))
            except DBusException:
                continue

        self._set_player()

    def _start_listener(self):
        self._dbus.add_signal_receiver(
            handler_function=self._dbus_name_owner_changed,
            dbus_interface="org.freedesktop.DBus",
            signal_name="NameOwnerChanged",
        )
        self._get_players()

        # Start listening things after initiating players.

        self._dbus.add_signal_receiver(
            self._player_on_change,
            dbus_interface=Interfaces.PROPERTIES,
            path=Interfaces.OBJECT_PATH,
            signal_name=Interfaces.SIGNAL,
            sender_keyword="sender",
        )

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

    def mpris(self):
        """
        Get the current output format and return it.
        """
        if self._kill:
            raise KeyboardInterrupt

        current_player = self._player
        current_player_id = current_player.id
        cached_until = self.py3.CACHE_FOREVER
        color = self.py3.COLOR_BAD
        exception = None

        if current_player:
            try:
                state_map = self._state_icon_color_map[self._player.state]
                placeholders = {
                    "state": state_map["state_icon"]
                }
                self._states["toggle"]["icon"] = state_map["toggle_icon"]
                color = state_map["color"]
                (text, cached_until) = current_player.get_text()
            except Exception as e:
                exception = e

            if not exception and current_player_id == self._player.id:
                composite = self.py3.safe_format(
                    self.format, dict(self._empty_response, **placeholders, **text)
                )
            else:
                # Something went wrong or the player changed during our processing
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
        if exception:
            self.py3.log(exception)
            self.py3.error(exception, 10)
        else:
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
                            next_index = (current_player_index - 1) % len(
                                switchable_players
                            )

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
