# -*- coding: utf-8 -*-
"""
Display song/video and control MPRIS compatible players.

There are two ways to control the media player. Either by clicking with a mouse
button in the text information or by using buttons. For former you have
to define the button parameters in your config.

Configuration parameters:
    button_next: mouse button to play the next entry (default 4)
    button_previous: mouse button to play the previous entry (default 5)
    button_stop: mouse button to stop the player (default None)
    button_toggle: mouse button to toggle between play and pause mode (default 1)
    format: see placeholders below
        (default '{previous}{toggle}{next} {state} [{artist} - ][{title}]')
    format_none: define output if no player is running
        (default 'no player running')
    icon_next: specify icon for next button (default ' » ')
    icon_pause: specify icon for pause button (default ' ▮ ')
    icon_play: specify icon for play button (default ' ▶ ')
    icon_previous: specify icon for previous button (default ' « ')
    icon_stop: specify icon for stop button (default ' ◾ ')
    player_priority: priority of the players.
        Keep in mind that the state has a higher priority than
        player_priority. So when player_priority is "[mpd, bomi]" and mpd is
        paused and bomi is playing than bomi wins. (default [])
    state_pause: text for placeholder {state} when song is paused (default '▮')
    state_play: text for placeholder {state} when song is playing (default '▶')
    state_stop: text for placeholder {state} when song is stopped (default '◾')

Format placeholders:
    {album} album name
    {artist} artiste name (first one)
    {length} time duration of the song
    {player} show name of the player
    {state} playback status of the player
    {time} played time of the song
    {title} name of the song

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
    pydbus: pythonic d-bus library

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
from time import time
from gi.repository import GObject
from gi.repository.GLib import GError
from threading import Thread
import re
import sys
from pydbus import SessionBus


SERVICE_BUS = "org.mpris.MediaPlayer2"
SERVICE_BUS_URL = "/org/mpris/MediaPlayer2"

WORKING_STATES = ["Playing", "Paused", "Stopped"]

PLAYING = 0
PAUSED = 1
STOPPED = 2


def _get_time_str(microseconds):
    seconds = int(microseconds / 1000000)
    time = str(timedelta(seconds=seconds))
    if time[0] == "0":
        time = time[2:]
        if time[0] == "0":
            time = time[1:]

    return time


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_previous = 5
    button_stop = None
    button_toggle = 1
    format = "{previous}{toggle}{next} {state} [{artist} - ][{title}]"
    format_none = "no player running"
    icon_next = u" » "
    icon_pause = u" ▮ "
    icon_play = u" ▶ "
    icon_previous = u" « "
    icon_stop = u" ◾ "
    player_priority = []
    state_pause = u"▮"
    state_play = u"▶"
    state_stop = u"◾"

    def post_config_hook(self):
        self._dbus = None
        self._data = {}
        self._control_states = {}
        self._kill = False
        self._mpris_players = {}
        self._mpris_names = {}
        self._mpris_name_index = {}
        self._player = None
        self._player_details = {}
        self._tries = 0
        # start last
        self._dbus = SessionBus()
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
        }

    def _init_data(self):
        self._data = {
            "album": None,
            "artist": None,
            "error_occurred": False,
            "length": None,
            "player": None,
            "state": STOPPED,
            "title": None,
        }

        if self._player is None:
            self._control_states = {}
            return

        try:
            self._data["player"] = self._player.Identity
            playback_status = self._player.PlaybackStatus
            self._data["state"] = self._get_state(playback_status)
            metadata = self._player.Metadata
            self._update_metadata(metadata)
        except Exception:
            self._data["error_occurred"] = True

    def _get_button_state(self, control_state):
        try:
            # Workaround: The last parameter returns True for the Stop button.
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

        if self._data.get("error_occurred"):
            color = self.py3.COLOR_BAD

        try:
            ptime_ms = self._player.Position
            ptime = _get_time_str(ptime_ms)
        except Exception:
            ptime = None

        if (
            self.py3.format_contains(self.format, "time")
            and self._data.get("state") == PLAYING
        ):
            # Don't get trapped in aliasing errors!
            update = time() + 0.5
        else:
            update = self.py3.CACHE_FOREVER

        placeholders = {
            "player": self._data.get("player"),
            "state": state_symbol,
            "album": self._data.get("album"),
            "artist": self._data.get("artist"),
            "length": self._data.get("length"),
            "time": ptime,
            "title": self._data.get("title") or "No Track",
            "full_name": self._player_details.get("full_name"),  # for debugging ;p
        }

        return (placeholders, color, update)

    def _get_control_states(self):
        state = "pause" if self._data.get("state") == PLAYING else "play"
        self._states["toggle"] = self._states[state]
        return self._states

    def _get_response_buttons(self):
        response = {}

        for button in self._control_states.keys():
            control_state = self._control_states[button]

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

    def _name_owner_changed(self, *args):
        player_id = args[5][0]
        player_add = args[5][2]
        player_remove = args[5][1]
        if player_add:
            self._add_player(player_id)
        if player_remove:
            self._remove_player(player_id)
        self._set_player()

    def _set_player(self):
        """
        Sort the current players into priority order and set self._player
        Players are ordered by working state then prefernce supplied by user
        and finally by instance if a player has more than one running.
        """
        players = []
        for name, p in self._mpris_players.items():
            # we set the priority here as we need to establish the player name
            # which might not be immediately available.
            if "_priority" not in p:
                if self.player_priority:
                    try:
                        priority = self.player_priority.index(p["name"])
                    except ValueError:
                        try:
                            priority = self.player_priority.index("*")
                        except ValueError:
                            priority = None
                else:
                    priority = 0
                if priority is not None:
                    p["_priority"] = priority
            if p.get("_priority") is not None:
                players.append((p["_state_priority"], p["_priority"], p["index"], name))
        if players:
            top_player = self._mpris_players.get(sorted(players)[0][3])
        else:
            top_player = {}

        self._player = top_player.get("_dbus_player")
        self._player_details = top_player

        self.py3.update()

    def _player_monitor(self, player_id):
        def player_on_change(*args):
            """
            Monitor a player and update its status.
            """
            data = args[1]
            status = data.get("PlaybackStatus")
            if status:
                player = self._mpris_players[player_id]

                # Note: Workaround. Since all players get noted if playback status
                #       has been changed we have to check if we are the choosen one
                try:
                    dbus_status = player["_dbus_player"].PlaybackStatus
                except GError:
                    # Prevent errors when calling methods of deleted dbus objects
                    return
                if status != dbus_status:
                    # FIXME: WE DON'T RECOGNIZE ANY TITLE CHANGE
                    return

                player["status"] = status
                player["_state_priority"] = WORKING_STATES.index(status)
            self._set_player()

        return player_on_change

    def _add_player(self, player_id):
        """
        Add player to mpris_players
        """
        if not player_id.startswith(SERVICE_BUS):
            return False

        player = self._dbus.get(player_id, SERVICE_BUS_URL)

        if player.Identity not in self._mpris_names:
            self._mpris_names[player.Identity] = player_id.split(".")[-1]
            for p in self._mpris_players.values():
                if not p["name"] and p["identity"] in self._mpris_names:
                    p["name"] = self._mpris_names[p["identity"]]
                    p["full_name"] = u"{} {}".format(p["name"], p["index"])

        identity = player.Identity
        name = self._mpris_names.get(identity)
        if (
            self.player_priority != []
            and name not in self.player_priority
            and "*" not in self.player_priority
        ):
            return False

        if identity not in self._mpris_name_index:
            self._mpris_name_index[identity] = 0

        status = player.PlaybackStatus
        state_priority = WORKING_STATES.index(status)
        index = self._mpris_name_index[identity]
        self._mpris_name_index[identity] += 1
        try:
            subscription = player.PropertiesChanged.connect(
                self._player_monitor(player_id)
            )
        except AttributeError:
            subscription = {}

        self._mpris_players[player_id] = {
            "_dbus_player": player,
            "_id": player_id,
            "_state_priority": state_priority,
            "index": index,
            "identity": identity,
            "name": name,
            "full_name": u"{} {}".format(name, index),
            "status": status,
            "subscription": subscription,
        }

        return True

    def _remove_player(self, player_id):
        """
        Remove player from mpris_players
        """
        player = self._mpris_players.get(player_id)
        if player:
            if player.get("subscription"):
                player["subscription"].disconnect()
            del self._mpris_players[player_id]

    def _get_players(self):
        bus = self._dbus.get("org.freedesktop.DBus")
        for player in bus.ListNames():
            self._add_player(player)

        self._set_player()

    def _start_listener(self):
        self._dbus.con.signal_subscribe(
            None,
            "org.freedesktop.DBus",
            "NameOwnerChanged",
            None,
            None,
            0,
            self._name_owner_changed,
        )
        self._get_players()
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
                url = metadata.get("xesam:url")
                is_stream = url is not None and "file://" not in url
                self._data["title"] = metadata.get("xesam:title")
                self._data["album"] = metadata.get("xesam:album")

                if metadata.get("xesam:artist") is not None:
                    self._data["artist"] = metadata.get("xesam:artist")[0]
                else:
                    # we assume here that we playing a video and these types of
                    # media we handle just like streams
                    is_stream = True

                length_ms = metadata.get("mpris:length")
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

    def kill(self):
        self._kill = True

    def mpris(self):
        """
        Get the current output format and return it.
        """
        if self._kill:
            raise KeyboardInterrupt
        current_player_id = self._player_details.get("id")
        cached_until = self.py3.CACHE_FOREVER

        if self._player is None:
            text = self.format_none
            color = self.py3.COLOR_BAD
            composite = [{"full_text": text, "color": color}]
            self._data = {}
        else:
            self._init_data()
            (text, color, cached_until) = self._get_text()
            self._control_states = self._get_control_states()
            buttons = self._get_response_buttons()
            composite = self.py3.safe_format(self.format, dict(text, **buttons))

        if self._data.get(
            "error_occurred"
        ) or current_player_id != self._player_details.get("id"):
            # Something went wrong or the player changed during our processing
            # This is usually due to something like a player being killed
            # whilst we are checking its details
            # Retry but limit the number of attempts
            self._tries += 1
            if self._tries < 3:
                return self.mpris()
            # Max retries hit we need to output something
            composite = [
                {"full_text": "Something went wrong", "color": self.py3.COLOR_BAD}
            ]
            cached_until = self.py3.time_in(1)

        response = {
            "cached_until": cached_until,
            "color": color,
            "composite": composite,
        }

        # we are outputing so reset tries
        self._tries = 0
        return response

    def on_click(self, event):
        """
        Handles click events
        """
        index = event["index"]
        button = event["button"]

        if index not in self._control_states.keys():
            if button == self.button_toggle:
                index = "toggle"
            elif button == self.button_stop:
                index = "stop"
            elif button == self.button_next:
                index = "next"
            elif button == self.button_previous:
                index = "previous"
            else:
                return
        elif button != 1:
            return

        control_state = self._control_states.get(index)
        if self._player and self._get_button_state(control_state):
            getattr(self._player, self._control_states[index]["action"])()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
