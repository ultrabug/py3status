r"""
Display song/video and control players supported by playerctl

Playerctl is a command-line utility for controlling media players
that implement the MPRIS D-Bus Interface Specification. With Playerctl
you can bind player actions to keys and get metadata about the currently
playing song or video.

Configuration parameters:
    button_loop: mouse button to cycle the loop status of the player (default None)
    button_next: mouse button to skip to the next track (default None)
    button_pause: mouse button to pause the playback (default None)
    button_play: mouse button to play the playback (default None)
    button_play_pause: mouse button to play/pause the playback (default 1)
    button_previous: mouse button to skip to the previous track (default None)
    button_seek_backward: mouse button to playback's position backward (default None)
    button_seek_forward: mouse button to playback's position forward (default None)
    button_shuffle: mouse button to toggle the shuffle mode of the player (default None)
    button_stop: mouse button to stop the playback (default 3)
    button_volume_down: mouse button to decrease the volume of the player (default None)
    button_volume_up: mouse button to increase the volume of the player (default None)
    format: display format for this module (default '{format_player}')
    format_player: display format for players
        *(default '[\?color=status [\?if=status=Playing > ][\?if=status=Paused \|\| ]'
        '[\?if=status=Stopped .. ][[{artist}][\?soft  - ][{title}|{player}]]]')*
    format_player_separator: show separator if more than one player (default ' ')
    players: list of players to track. An empty list tracks all players (default [])
    replacements: specify a list/dict of string placeholders to modify (default None)
    seek_delta: time (in seconds) to change the playback's position by (default 5)
    thresholds: specify color thresholds to use for different placeholders
        (default {"status": [("Playing", "good"), ("Paused", "degraded"), ("Stopped", "bad")]})
    volume_delta: percentage (from 0 to 100) to change the player's volume by (default 10)

    Not all players support every button action

Format placeholders:
    {format_player} format for players

Format player placeholders:
    {album} album name
    {artist} artist name
    {duration} length of track/video in [HH:]MM:SS, e.g. 03:22
    {loop} loop status of the player, e.g. None, playlist, Track
    {player} name of the player
    {position} elapsed time in [HH:]MM:SS, e.g. 00:17
    {shuffle} boolean indicating if the player's shuffle mode is on
    {status} playback status, e.g. Playing, Paused, Stopped
    {title} track/video title
    {trackNumber} position of the track in the album or playlist
    {volume} volume level of the player from 0 to 100

    Not all media players support every placeholder

Requires:
    playerctl: mpris media player controller and lib for spotify, vlc, audacious,
        bmp, xmms2, and others.
    python-gobject: Python Bindings for GLib/GObject/GIO/GTK+

@author jdholtz

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': '> Don’t Eat the Yellow Snow - Frank Zappa'}

Paused
{'color': '#FFFF00', 'full_text': '|| Too Much Skunk Tonight - Birdy Nam Nam'}

Stopped
{'color': '#FF0000', 'full_text': '.. This Song Has No Title - Elton John'}
"""

import time
from fnmatch import fnmatch
from threading import Thread

import gi

gi.require_version("Playerctl", "2.0")
from gi.repository import GLib, Playerctl  # noqa e402


class Py3status:
    """ """

    # available configuration parameters
    button_loop = None
    button_next = None
    button_pause = None
    button_play = None
    button_play_pause = 1
    button_previous = None
    button_seek_backward = None
    button_seek_forward = None
    button_shuffle = None
    button_stop = 3
    button_volume_down = None
    button_volume_up = None
    format = "{format_player}"
    format_player = (
        r"[\?color=status [\?if=status=Playing > ][\?if=status=Paused \|\| ]"
        r"[\?if=status=Stopped .. ][[{artist}][\?soft  - ][{title}|{player}]]]"
    )
    format_player_separator = " "
    players = []
    replacements = None
    seek_delta = 5
    thresholds = {"status": [("Playing", "good"), ("Paused", "degraded"), ("Stopped", "bad")]}
    volume_delta = 10

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    # Escape the title by default because many contain special characters
                    "placeholder_formats": {"title": ":escape"},
                    "format_strings": ["format_player"],
                }
            ]
        }

    def post_config_hook(self):
        self.thresholds_init = self.py3.get_color_names_list(self.format_player)
        self.replacements_init = self.py3.get_replacements_list(self.format_player)
        self.position = self.py3.format_contains(self.format_player, "position")
        self.cache_timeout = getattr(self, "cache_timeout", 1)

        # Initialize the manager + event listeners
        self.manager = Playerctl.PlayerManager()
        self.manager.connect("name-appeared", self._on_name_appeared)
        self.manager.connect("name-vanished", self._on_name_vanished)

        # Initialize all currently active players
        for player_name in self.manager.props.player_names:
            self._init_player(player_name)

        self._start_loop()

    def _player_should_be_tracked(self, player_name):
        for _filter in self.players:
            if fnmatch(player_name.name, _filter):
                return True

        return len(self.players) == 0

    def _init_player(self, player_name):
        if not self._player_should_be_tracked(player_name):
            return

        player = Playerctl.Player.new_from_name(player_name)

        # Initialize player event listeners
        player.connect("loop-status", self._loop_status_changed, self.manager)
        player.connect("metadata", self._on_metadata, self.manager)
        player.connect("playback-status", self._status_changed, self.manager)
        player.connect("seeked", self._on_seeked, self.manager)
        player.connect("shuffle", self._shuffle_changed, self.manager)
        player.connect("volume", self._volume_changed, self.manager)

        self.manager.manage_player(player)

    def _start_loop(self):
        loop = GLib.MainLoop()

        # The loop is blocking so it needs to be run a separate thread
        thread = Thread(target=loop.run)
        thread.daemon = True
        thread.start()

    def _on_name_appeared(self, manager, player_name):
        self._init_player(player_name)

    def _on_name_vanished(self, manager, name):
        # Add a very small delay to give Playerctl time to remove the player
        time.sleep(0.01)
        self.py3.update()

    def _loop_status_changed(self, player, loop_status, manager):
        self.py3.update()

    def _on_metadata(self, player, metadata, manager):
        self.py3.update()

    def _status_changed(self, player, status, manager):
        self.py3.update()

    def _on_seeked(self, player, position, manager):
        self.py3.update()

    def _shuffle_changed(self, player, shuffle, manager):
        self.py3.update()

    def _volume_changed(self, player, volume, manager):
        self.py3.update()

    @staticmethod
    def _microseconds_to_time(microseconds):
        seconds = microseconds // 1_000_000
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time = f"{h}:{m:02d}:{s:02d}"
        return time.lstrip("0").lstrip(":")

    def _get_player_position(self, player):
        try:
            # Playerctl doesn't support getting positions for all players
            microseconds = player.get_position()
            position = self._microseconds_to_time(microseconds)
        except GLib.GError:
            position = None

        return position

    def _set_data_from_metadata(self, player, data):
        """Set any data retrieved directly from the metadata for a player"""
        metadata = dict(player.props.metadata)

        data["trackNumber"] = metadata.get("xesam:trackNumber")

        duration_ms = metadata.get("mpris:length")
        if duration_ms:
            data["duration"] = self._microseconds_to_time(duration_ms)
        else:
            data["duration"] = None

    def _get_player_data(self, player):
        data = {}

        # Song attributes
        data["album"] = player.get_album()
        data["artist"] = player.get_artist()
        data["title"] = player.get_title()
        data["position"] = self._get_player_position(player)
        self._set_data_from_metadata(player, data)

        # Player attributes
        data["player"] = player.props.player_name
        data["loop"] = player.props.loop_status.value_nick
        data["shuffle"] = player.props.shuffle
        data["status"] = player.props.status
        data["volume"] = int(player.props.volume * 100)

        return data

    def _get_player_from_index(self, index):
        for player in self.manager.props.players:
            if player.props.player_name == index:
                return player

        return None

    def _change_player_volume(self, player, volume_factor):
        volume_change = volume_factor * self.volume_delta / 100
        new_volume = player.props.volume + volume_change
        try:
            # Playerctl can't set the volume for every player
            player.set_volume(new_volume)
        except GLib.GError:
            pass

    def _cycle_player_loop_status(self, player):
        new_loop_status = (player.props.loop_status + 1) % 3
        try:
            # Not all players support setting the loop status
            player.set_loop_status(new_loop_status)
        except GLib.GError:
            pass

    def _toggle_player_shuffle(self, player):
        try:
            # Not all players support setting the shuffle mode
            player.set_shuffle(not player.props.shuffle)
        except GLib.GError:
            pass

    def playerctl(self):
        tracked_players = self.manager.props.players

        players = []
        cached_until = self.py3.CACHE_FOREVER
        for player in tracked_players:
            if not player.props.can_play:
                continue

            player_data = self._get_player_data(player)

            # Check if the player should cause the module to continuously update
            if self.position and player_data["status"] == "Playing" and player_data["position"]:
                cached_until = self.cache_timeout

            # Replace the values
            for x in self.replacements_init:
                if x in player_data:
                    player_data[x] = self.py3.replace(player_data[x], x)

            # Set the color of a player
            for key in self.thresholds_init:
                if key in player_data:
                    self.py3.threshold_get_color(player_data[key], key)

            format_player = self.py3.safe_format(self.format_player, player_data)
            self.py3.composite_update(format_player, {"index": player_data["player"]})

            players.append(format_player)

        format_player_separator = self.py3.safe_format(self.format_player_separator)
        format_players = self.py3.composite_join(format_player_separator, players)

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, {"format_player": format_players}),
        }

    def on_click(self, event):
        """
        Control playerctl with mouse clicks.
        """
        button = event["button"]
        index = event["index"]

        # Always prevent a refresh because this module updates whenever
        # a player's status or metadata changes
        self.py3.prevent_refresh()

        player = self._get_player_from_index(index)
        if not player or not player.props.can_control:
            return

        if button == self.button_play and player.props.can_play:
            player.play()
        elif button == self.button_pause and player.props.can_pause:
            player.pause()
        elif button == self.button_play_pause and player.props.can_play:
            player.play_pause()
        elif button == self.button_stop:
            player.stop()
        elif button == self.button_next and player.props.can_go_next:
            player.next()
        elif button == self.button_previous and player.props.can_go_previous:
            player.previous()
        elif button == self.button_seek_forward and player.props.can_seek:
            player.seek(self.seek_delta * 10**6)
        elif button == self.button_seek_backward and player.props.can_seek:
            player.seek(self.seek_delta * -1 * 10**6)
        elif button == self.button_volume_up:
            self._change_player_volume(player, 1)
        elif button == self.button_volume_down:
            self._change_player_volume(player, -1)
        elif button == self.button_loop:
            self._cycle_player_loop_status(player)
        elif button == self.button_shuffle:
            self._toggle_player_shuffle(player)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
