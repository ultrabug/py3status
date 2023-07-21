r"""
Display song/video and control players supported by playerctl

Playerctl is a command-line utility for controlling media players 
that implement the MPRIS D-Bus Interface Specification. With Playerctl
you can bind player actions to keys and get metadata about the currently
playing song or video.

Configuration parameters:
    button_next: mouse button to skip to the next track (default None)
    button_pause: mouse button to pause the playback (default None)
    button_play: mouse button to play the playback (default None)
    button_play_pause: mouse button to play/pause the playback (default 1)
    button_previous: mouse button to skip to the previous track (default None)
    button_stop: mouse button to stop the playback (default 3)
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module (default: '{format_player}')
    format_player: display format for players:
        *(default '[\?if=is_playing > ][\?if=is_paused \|\| ]'
        '[\?if=is_stopped .. ][[{artist}][\?soft  - ][{title}]]')*
    format_separator: show separator if more than one (default: ' ')
    players: list of players to track. An empty list tracks all players (default: [])
    sleep_timeout: sleep interval for this module. When playerctl is not tracking any
        players, this interval will be used. This allows some flexible timing where
        one might want to refresh constantly with some placeholders or to refresh
        only once every minute rather than every few seconds. (default 20)

Control placeholders:
    {is_paused} True if the player is paused. Otherwise, false
    {is_playing} True if the player is playing. Otherwise, false
    {is_stopped} True if the player is stopped. Otherwise, false

Format placeholders:
    {album} album name
    {artist} artist name
    {duration} length of track/video in [HH:]MM:SS, e.g. 03:22
    {player} name of the player
    {position} elapsed time in [HH:]MM:SS, e.g. 00:17
    {title} track/video title

    Not all media players support every placeholder

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Stopped, defaults to color_bad

Requires:
    playerctl: mpris media player controller and lib for spotify, vlc, audacious,
        bmp, xmms2, and others.

@author jdholtz

SAMPLE OUTPUT
[
    {'color': '#00FF00', 'full_text': '> My Lucky Pants Failed Me Again - Tom Rosenthal'}
    {'color': '#FFFF00', 'full_text': '|| Too Much Skunk Tonight - Birdy Nam Nam'}
]
"""
from threading import Thread

import gi

gi.require_version("Playerctl", "2.0")
from gi.repository import GLib, Playerctl


class Py3status:
    """ """

    # available configuration parameters
    button_next = None
    button_pause = None
    button_play = None
    button_play_pause = 1
    button_previous = None
    button_stop = 3
    cache_timeout = 5
    format = "{format_player}"
    format_player = (
        r"[\?if=is_playing > ][\?if=is_paused \|\| ]"
        r"[\?if=is_stopped .. ][[{artist}][\?soft  - ][{title}]]"
    )
    format_separator = " "
    players = []
    sleep_timeout = 20

    def post_config_hook(self):
        if not self.py3.check_commands("playerctl"):
            raise Exception("command 'playerctl' not installed")

        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD

        self._init_manager()

    def _init_manager(self):
        self.manager = Playerctl.PlayerManager()
        self.manager.connect("name-appeared", self._on_name_appeared)
        self.manager.connect("name-vanished", self._on_name_vanished)

        # Initialize all currently active players
        for player_name in self.manager.props.player_names:
            self._init_player(player_name)

        self._start_loop()

    def _init_player(self, player_name):
        if len(self.players) > 0 and player_name.name not in self.players:
            return

        player = Playerctl.Player.new_from_name(player_name)

        # Set up all event listeners
        player.connect("playback-status", self._status_changed, self.manager)
        player.connect("metadata", self._on_metadata, self.manager)

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
        self.py3.update()

    def _on_metadata(self, player, metadata, manager):
        self.py3.update()

    def _status_changed(self, player, status, manager):
        self.py3.update()

    def _get_player_position(self, player):
        try:
            # Playerctl doesn't support getting positions for all players
            microseconds = player.get_position()
            position = self._microseconds_to_time(microseconds)
        except GLib.GError:
            position = None

        return position

    @staticmethod
    def _microseconds_to_time(microseconds):
        seconds = microseconds // 1_000_000
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time = f"{h}:{m:02d}:{s:02d}"
        return time.lstrip("0").lstrip(":")

    def _set_color(self, player, data):
        """Set the color and the control variables for a player"""
        status = player.props.playback_status
        if status == Playerctl.PlaybackStatus.PLAYING:
            data["color"] = self.color_playing
            data["is_playing"] = True
        elif status == Playerctl.PlaybackStatus.PAUSED:
            data["color"] = self.color_paused
            data["is_paused"] = True
        else:
            data["color"] = self.color_stopped
            data["is_stopped"] = True

    def _set_data_from_metadata(self, player, data):
        """Set any data retrieved directly from the metadata for a player"""
        metadata = dict(player.props.metadata)

        duration_ms = metadata.get("mpris:length")
        if duration_ms:
            data["duration"] = self._microseconds_to_time(duration_ms)
        else:
            data["duration"] = None

    def _get_player_data(self, player):
        data = {}

        data["album"] = player.get_album()
        data["artist"] = player.get_artist()
        data["title"] = player.get_title()
        data["player"] = player.props.player_name

        self._set_color(player, data)

        data["position"] = self._get_player_position(player)
        self._set_data_from_metadata(player, data)

        return data

    def playerctl(self):
        tracked_players = self.manager.props.players
        cached_until = self.cache_timeout if tracked_players else self.sleep_timeout

        players = []
        for player in tracked_players:
            player_data = self._get_player_data(player)

            # Delete after referencing because it shouldn't be a valid placeholder
            color = player_data["color"]
            del player_data["color"]

            format_player = self.py3.safe_format(self.format_player, player_data)
            self.py3.composite_update(format_player, {"index": player_data["player"]})
            self.py3.composite_update(format_player, {"color": color})
            players.append(format_player)

        format_separator = self.py3.safe_format(self.format_separator)
        format_players = self.py3.composite_join(format_separator, players)

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(
                self.format, {"format_player": format_players}
            ),
        }

    def _get_player_from_index(self, index):
        for player in self.manager.props.players:
            if player.props.player_name == index:
                return player

        # Should never be reached as the user can't click on a player
        # that doesn't exist
        return None

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
        if not player.props.can_control:
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


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
