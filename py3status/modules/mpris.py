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
    hide_non_canplay: Used to hide chrome/chomium players on idle state. (default ['chrome', 'chromium'])
    icon_next: specify icon for next button (default u'\u25b9')
    icon_pause: specify icon for pause button (default u'\u25eb')
    icon_play: specify icon for play button (default u'\u25b7')
    icon_previous: specify icon for previous button (default u'\u25c3')
    icon_stop: specify icon for stop button (default u'\u25a1')
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
from mpris2 import Player, MediaPlayer2, get_players_uri, Interfaces
from mpris2.types import Metadata_Map

STRING_GEVENT = "this module does not work with gevent"

WORKING_STATES = ["Playing", "Paused", "Stopped"]

PLAYING = 0
PAUSED = 1
STOPPED = 2


def _get_time_str(microseconds):
    delta = timedelta(seconds=microseconds // 1_000_000)
    delta_str = str(delta).lstrip("0").lstrip(":")
    if delta_str.startswith("0"):
        delta_str = delta_str[1:]
    return delta_str


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
    hide_non_canplay = ["chrome", "chromium"]
    icon_next = "\u25b9"
    icon_pause = "\u25eb"
    icon_play = "\u25b7"
    icon_previous = "\u25c3"
    icon_stop = "\u25a1"
    player_priority = []
    state_pause = "\u25eb"
    state_play = "\u25b7"
    state_stop = "\u25a1"

    def post_config_hook(self):
        # TODO: Look again if it is needed
        if self.py3.is_gevent():
            raise Exception(STRING_GEVENT)
        self._dbus = None
        self._data = {}
        self._control_states = {}
        self._ownerToPlayerId = {}
        self._kill = False
        self._mpris_players = {}
        self._mpris_names = {}
        self._mpris_name_index = {}
        self._player = None
        self._player_details = {}
        self._tries = 0
        # start last
        self._dbus_loop = DBusGMainLoop()
        self._dbus = SessionBus(mainloop=self._dbus_loop)
        self._start_listener()
        self._states = {
            "pause": {
                "action": "Pause",
                "clickable": "CanPause",
                "icon": self.icon_pause,
            },
            "play": {"action": "Play", "clickable": "CanPlay", "icon": self.icon_play},
            "stop": {
                "action": "Stop",
                "clickable": "True",  # The MPRIS API lacks 'CanStop' function.
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
            "toggle": {"action": "PlayPause", "clickable": "True", "icon": None},
        }

        self._format_contains_metadata = False
        for key in ["album", "artist", "titile"]:
            if self.py3.format_contains(self.format, key):
                self._format_contains_metadata = True
                break

        self._format_contains_time = self.py3.format_contains(self.format, "time")

    def _init_data(self):
        self._data = {
            "album": None,
            "artist": None,
            "exception": None,
            "length": None,
            "player": None,
            "state": STOPPED,
            "title": None,
            "nowplaying": None,
        }

        try:
            self._data["player"] = self._media_player.Identity
            playback_status = self._player.PlaybackStatus
            self._data["state"] = self._get_state(playback_status)
            if self._format_contains_metadata:
                self._update_metadata(self._player.Metadata)

        except Exception as e:
            self._data["exception"] = e

    def _get_button_state(self, control_state):
        try:
            # Workaround: The last parameter returns True for the Stop / Toggle button.
            clickable = getattr(self._player, control_state["clickable"], True)
        except Exception:
            clickable = False

        state = self._data.get("state")
        if control_state["action"] == "Play" and state == PLAYING:
            clickable = False
        elif control_state["action"] == "Pause" and state in [STOPPED, PAUSED]:
            clickable = False
        elif control_state["action"] == "Stop" and state == STOPPED:
            clickable = False

        return clickable

    def _get_state(self, playback_status):
        if playback_status == "Playing":
            return PLAYING
        elif playback_status == "Paused":
            return PAUSED
        else:
            return STOPPED

    def _get_text(self):
        """
        Get the current metadata
        """
        if self._data.get("state") == PLAYING:
            color = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
            state_symbol = self.state_play
        elif self._data.get("state") == PAUSED:
            color = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
            state_symbol = self.state_pause
        else:
            color = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
            state_symbol = self.state_stop

        ptime = None
        cache_until = self.py3.CACHE_FOREVER

        if self._format_contains_time:
            try:
                ptime_ms = getattr(self._player, "Position", None)
            except DBusException:
                ptime_ms = None

            if ptime_ms is not None and ptime_ms != 0:
                ptime = _get_time_str(ptime_ms)
                if self._data.get("state") == PLAYING:
                    # cache_until = 63238
                    cache_until = time.perf_counter() + 0.5

        placeholders = {
            "player": self._data.get("player"),
            "state": state_symbol,
            "album": self._data.get("album"),
            "artist": self._data.get("artist"),
            "length": self._data.get("length"),
            "time": ptime,
            "title": self._data.get("title") or "No Track",
            "nowplaying": self._data.get("nowplaying"),
            # for debugging ;p
            "full_name": self._player_details.get("full_name"),
        }

        return (placeholders, color, cache_until)

    def _get_control_states(self):
        state = "pause" if self._data.get("state") == PLAYING else "play"
        self._states["toggle"]["icon"] = self._states[state]["icon"]
        return self._states

    def _get_response_buttons(self):
        response = {}

        for button, control_state in self._control_states.items():
            if self._get_button_state(control_state):
                color = self.py3.COLOR_CONTROL_ACTIVE or self.py3.COLOR_GOOD
            else:
                color = self.py3.COLOR_CONTROL_INACTIVE or self.py3.COLOR_BAD

            response[button] = {
                "color": color,
                "full_text": control_state["icon"],
                "index": button,
            }

        return response

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

    def _set_player(self):
        """
        Sort the current players into priority order and set self._player
        Players are ordered by working state, then by preference supplied by
        user and finally by instance if a player has more than one running.
        """
        players = []
        for name, p in self._mpris_players.items():
            # we set the priority here as we need to establish the player name
            # which might not be immediately available.
            if "_priority" not in p:
                if self.player_priority:
                    try:
                        priority = self.player_priority.index(p["name_from_id"])
                    except ValueError:
                        try:
                            priority = self.player_priority.index("*")
                        except ValueError:
                            priority = None
                else:
                    priority = 0
                if priority is not None:
                    p["_priority"] = priority
            if p.get("_priority") is not None and not p.get("_hide"):
                players.append((p["_state_priority"], p["_priority"], p["index"], name))
        if players:
            top_player = self._mpris_players.get(sorted(players)[0][3])
        else:
            top_player = {}

        self._player = top_player.get("_dbus_player")
        self._media_player = top_player.get("_dbus_media_player")
        self._player_details = top_player
        self.py3.update()

    def _should_hide_mediaplayer(self, player_id, canPlay):
        return (
            not canPlay
            and self._mpris_players[player_id]["name_from_id"] in self.hide_non_canplay
        )

    def _player_on_change(self, interface_name, data, invalidated_properties, sender):
        """
        Monitor a player and update its status.
        """

        if interface_name != Interfaces.PLAYER:
            return

        sender_player_id = self._ownerToPlayerId.get(sender)
        if not sender_player_id:
            return
        sender_player = self._mpris_players.get(sender_player_id)
        if not sender_player:
            return

        data = dict(data)
        data_keys = data.keys()
        call_update = False
        call_set_player = False

        if "PlaybackStatus" in data_keys:
            status = data.get("PlaybackStatus")
            if status:
                sender_player["status"] = status
                sender_player["_state_priority"] = WORKING_STATES.index(status)
                call_set_player = True

        # it usually comes with Rate and Rate can come without metadata.
        elif "Metadata" in data_keys:
            if self._format_contains_metadata:
                is_active_player = sender_player_id == self._player_details.get("_id")
                call_update = is_active_player

        elif "CanPlay" in data_keys:
            sender_player["_hide"] = self._should_hide_mediaplayer(
                sender_player_id, data.get("CanPlay")
            )
            call_set_player = True

        else:
            if "Rate" in data_keys:
                pass

        if call_update and not call_set_player:
            self.py3.update()
        elif call_set_player:
            self._set_player()

    def _add_player(self, player_id, owner):
        """
        Add player to mpris_players
        """
        dPlayer = Player(dbus_interface_info={"dbus_uri": player_id})
        dMediaPlayer = MediaPlayer2(dbus_interface_info={"dbus_uri": player_id})
        identity = str(dMediaPlayer.Identity)

        if identity not in self._mpris_names:
            self._mpris_names[identity] = player_id.split(".")[-1]
            for p in self._mpris_players.values():
                if not p["name"] and p["identity"] in self._mpris_names:
                    p["name"] = self._mpris_names[p["identity"]]
                    p["full_name"] = "{} {}".format(p["name"], p["index"])

        name = self._mpris_names.get(identity)
        if (
            self.player_priority != []
            and name not in self.player_priority
            and "*" not in self.player_priority
        ):
            return False

        if identity not in self._mpris_name_index:
            self._mpris_name_index[identity] = 0

        status = dPlayer.PlaybackStatus
        state_priority = WORKING_STATES.index(status)
        index = self._mpris_name_index[identity]
        self._mpris_name_index[identity] += 1

        self._ownerToPlayerId[owner] = player_id

        self._mpris_players[player_id] = {
            "_dbus_player": dPlayer,
            "_dbus_media_player": dMediaPlayer,
            "_hide": None,
            "_id": player_id,
            "_state_priority": state_priority,
            "name_from_id": player_id.split(".")[3],
            "index": index,
            "identity": identity,
            "name": name,
            "full_name": f"{name} {index}",
            "status": status,
        }
        self._mpris_players[player_id]["_hide"] = self._should_hide_mediaplayer(
            player_id, dPlayer.CanPlay
        )

        return True

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

    def _update_metadata(self, metadata):
        is_stream = False

        try:
            if len(metadata) > 0:
                url = metadata.get(Metadata_Map.URL)
                is_stream = url is not None and "file://" not in url
                self._data["title"] = metadata.get(Metadata_Map.TITLE)
                self._data["album"] = metadata.get(Metadata_Map.ALBUM)

                if metadata.get(Metadata_Map.ARTIST):
                    self._data["artist"] = metadata.get(Metadata_Map.ARTIST)[0]
                else:
                    # we assume here that we playing a video and these types of
                    # media we handle just like streams
                    is_stream = True

                length_ms = metadata.get(Metadata_Map.LENGTH)
                if length_ms is not None:
                    self._data["length"] = _get_time_str(length_ms)
            else:
                # use stream format if no metadata is available
                is_stream = True
        except Exception:
            self._data["error_occurred"] = True

        if is_stream and self._data.get("title"):
            # delete the file extension
            self._data["title"] = re.sub(r"\....$", "", self._data.get("title"))
            self._data["nowplaying"] = metadata.get("vlc:nowplaying")

    def _set_data_entry_point_by_name_key(self, new_active_player_key, update=True):
        if new_active_player_key == self._player_details:
            return

        top_player = self._mpris_players.get(new_active_player_key) or {}
        self._player = top_player.get("_dbus_player")
        self._media_player = top_player.get("_dbus_media_player")
        self._player_details = top_player

    def _send_mpris_action(self, index):
        control_state = self._control_states.get(index)

        try:
            if self._player and self._get_button_state(control_state):
                getattr(self._player, self._control_states[index]["action"])()
        except DBusException as err:
            self.py3.log(
                f"Player {self._player_details['identity']} responded {str(err).split(':', 1)[-1]}"
            )

    def kill(self):
        self._kill = True

    def mpris(self):
        """
        Get the current output format and return it.
        """
        if self._kill:
            raise KeyboardInterrupt

        current_player_id = self._player_details.get("_id")
        cached_until = self.py3.CACHE_FOREVER
        color = self.py3.COLOR_BAD

        if self._player:
            self._init_data()
            if not self._data.get(
                "exception"
            ) and current_player_id == self._player_details.get("_id"):
                (text, color, cached_until) = self._get_text()
                self._control_states = self._get_control_states()
                buttons = self._get_response_buttons()
                composite = self.py3.safe_format(self.format, dict(text, **buttons))
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
            composite = [{"full_text": self.format_none, "color": self.py3.COLOR_BAD}]
            self._data = {}
            self._control_states = {}

        # we are outputting so reset tries
        self._tries = 0
        if self._data.get("exception"):
            self.py3.log(self._data.get("exception"))
            self.py3.error(str(self._data.get("exception")), 10)
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

        if index not in self._control_states:
            self.py3.prevent_refresh()
            if button == self.button_toggle:
                return self._send_mpris_action("toggle")
            elif button == self.button_stop:
                return self._send_mpris_action("stop")
            elif button == self.button_next:
                return self._send_mpris_action("next")
            elif button == self.button_previous:
                return self._send_mpris_action("previous")
            elif button == self.button_switch_to_top_player:
                return self._set_player()

            elif button == self.button_prev_player or button == self.button_next_player:
                switchable_players = []
                order_asc = button == self.button_next_player
                current_player_index = False
                for player in self._mpris_players.keys():
                    if (
                        self._mpris_players[player]["status"]
                        == self._player_details.get("status")
                        and not self._mpris_players[player]["_hide"]
                    ):
                        if not current_player_index:
                            if self._mpris_players[player][
                                "_id"
                            ] == self._player_details.get("_id"):
                                current_player_index = len(switchable_players)
                                if order_asc:
                                    continue

                        switchable_players.append(player)
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
                            switchable_players[next_index]
                        )

                    except KeyError:
                        pass

            else:
                return

        elif button == 1:
            self._send_mpris_action(index)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    config = {"player_priority": "[*, vlc]"}
    module_test(Py3status, config)
