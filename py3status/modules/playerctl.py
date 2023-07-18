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
    button_shift: mouse button to manage the next player being tracked (default None)
    button_stop: mouse button to stop the playback (default 3)
    button_unshift: mouse button to manage the previous player being tracked (default None)
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module
        *(default '[\?if=is_started [\?if=is_playing > ][\?if=is_paused \|\| ]'
        '[\?if=is_stopped .. ][[{artist}][\?soft  - ][{title}]'
        '|\?show playerctl: no active players]]')*
    ignored_players: list of players to ignore. Playerctld will always be 
        ignored as it conflicts with this module (default: [])
    sleep_timeout: sleep interval for this module. When playerctl is not controlling
        any media players, this interval will be used. This allows some flexible
        timing where one might want to refresh constantly with some placeholders or to
        refresh only once every minute rather than every few seconds. (default 20)

Control placeholders:
    {is_paused} True if the current player is paused. Otherwise, false
    {is_playing} True if the current player is playing. Otherwise, false
    {is_started} True if there is at least one active player. Otherwise, false 
    {is_stopped} True if the current player is stopped. Otherwise, false

Format placeholders:
    {album} album name
    {artist} artist name
    {position} elapsed time in [HH:]MM:SS, eg 00:17
    {title} track/video title

    Not all media players support every placeholder

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Stopped, defaults to color_bad


Requires:
    playerctl: mpris media player controller and lib for spotify, vlc, audacious, bmp, xmms2, and others.

@author jdholtz

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': '> My Lucky Pants Failed Me Again - Tom Rosenthal'}

paused
{'color': '#FFFF00', 'full_text': '|| My Lucky Pants Failed Me Again - Tom Rosenthal'}

stopped
{'color': '#FF0000', 'full_text': '.. My Lucky Pants Failed Me Again - Tom Rosenthal'}

waiting
{'color': '#FF0000', 'full_text': '.. playerctl: no active players'}
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
    button_shift = None
    button_unshift = None
    button_stop = 3
    cache_timeout = 5
    format = (
        r"[\?if=is_started [\?if=is_playing > ][\?if=is_paused \|\| ]"
        r"[\?if=is_stopped .. ][[{artist}][\?soft  - ][{title}]"
        r"|\?show playerctl: no active players]]"
    )
    ignored_players = []
    sleep_timeout = 20

    def post_config_hook(self):
        if not self.py3.check_commands("playerctl"):
            raise Exception("command 'playerctl' not installed")

        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD

        # Playerctld conflicts with this module
        if "playerctld" not in self.ignored_players:
            self.ignored_players.append("playerctld")

        self._reset()
        self._init_manager()

    def _get_player_names(self):
        return [
            player_name
            for player_name in self.manager.props.player_names
            if player_name.name not in self.ignored_players
        ]

    def _get_players(self):
        return [
            player
            for player in self.manager.props.players
            if player.props.player_name not in self.ignored_players
        ]

    def _reset(self):
        self.status = None
        self.album = None
        self.artist = None
        self.title = None
        self.position = None
        self.active_player = None
        self.is_started = False

    def _init_manager(self):
        self.manager = Playerctl.PlayerManager()
        self.manager.connect("name-appeared", self._on_name_appeared)
        self.manager.connect("name-vanished", self._on_name_vanished)

        # Initialize all currently active players
        for player_name in self._get_player_names():
            self.py3.log(player_name.name)
            self._init_player(player_name)

        players = self._get_players()
        if len(players) > 0:
            # Start monitoring the first player
            self._set_active_player(players[0], False)
            self.is_started = True

        self._start_loop()

    def _init_player(self, player_name):
        player = Playerctl.Player.new_from_name(player_name)

        # Set up all event listeners
        player.connect("playback-status", self._status_changed, self.manager)
        player.connect("metadata", self._on_metadata, self.manager)

        self.manager.manage_player(player)

    def _set_active_player(self, player, update_module=True):
        self.py3.log(player.props.player_name)
        self.active_player = player
        self.album = player.get_album()
        self.artist = player.get_artist()
        self.title = player.get_title()
        self.status = player.props.playback_status

        try:
            # Playerctl doesn't support getting positions for all players
            microseconds = player.get_position()
            self.position = self._microseconds_to_time(microseconds)
        except GLib.GError:
            self.position = None

        if update_module:
            self.py3.update()

    def _start_loop(self):
        loop = GLib.MainLoop()

        # The loop is blocking so it needs to be run a separate thread
        thread = Thread(target=loop.run)
        thread.daemon = True
        thread.start()

    def _shift(self, shift):
        players = self._get_players()
        if len(players) == 0:
            return

        active_player_idx = 0
        if self.active_player in players:
            # Set the correct index if the player exists (has not been removed)
            active_player_idx = players.index(self.active_player)

        new_player_idx = (active_player_idx + shift) % len(players)
        self._set_active_player(players[new_player_idx])

    def _on_name_appeared(self, manager, player_name):
        if player_name.name in self.ignored_players:
            return

        self._init_player(player_name)

        players = self._get_players()
        if len(players) == 1:
            # It is the only player being tracked
            self._set_active_player(players[0])
            self.is_started = True

    def _on_name_vanished(self, manager, name):
        if len(self._get_players()) == 0:
            # No players are being tracked
            self._reset()
            self.py3.update()
            return

        # Shift to the next player (shift by 0 because this player
        # has been removed from tracking)
        self._shift(0)

    def _on_metadata(self, player, metadata, manager):
        self._set_active_player(player)

    def _status_changed(self, player, status, manager):
        self._set_active_player(player)

    def _shift_player(self):
        """Shift the active player forward by 1"""
        self._shift(1)

    def _unshift_player(self):
        """Shift the active player backward by 1"""
        self._shift(-1)

    @staticmethod
    def _microseconds_to_time(microseconds):
        seconds = microseconds // 1_000_000
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time = f"{h}:{m:02d}:{s:02d}"
        return time.lstrip("0").lstrip(":")

    def playerctl(self):
        is_paused = is_playing = is_stopped = None
        color = self.py3.COLOR_BAD
        cached_until = self.cache_timeout if self.is_started else self.sleep_timeout

        data = {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "position": self.position,
        }

        if self.status == Playerctl.PlaybackStatus.PLAYING:
            is_playing = True
            color = self.color_playing
        elif self.status == Playerctl.PlaybackStatus.PAUSED:
            is_paused = True
            color = self.color_paused
        elif self.status == Playerctl.PlaybackStatus.STOPPED:
            is_stopped = True
            color = self.color_stopped

        # TODO: & in the metadata properties causes module not to display
        return {
            "cached_until": self.py3.time_in(cached_until),
            "color": color,
            "full_text": self.py3.safe_format(
                self.format,
                dict(
                    is_paused=is_paused,
                    is_playing=is_playing,
                    is_started=self.is_started,
                    is_stopped=is_stopped,
                    **data,
                ),
            ),
        }

    def on_click(self, event):
        """
        Control playerctl with mouse clicks.
        """
        if not self.active_player:
            self.py3.prevent_refresh()
            return

        button = event["button"]
        if button == self.button_shift:
            self._shift_player()
            return

        if button == self.button_unshift:
            self._unshift_player()
            return

        if not self.active_player.props.can_control:
            self.py3.prevent_refresh()
            return

        player_props = self.active_player.props
        if button == self.button_play and player_props.can_play:
            self.active_player.play()
        elif button == self.button_pause and player_props.can_pause:
            self.active_player.pause()
        elif button == self.button_play_pause and player_props.can_play:
            self.active_player.play_pause()
        elif button == self.button_stop:
            self.active_player.stop()
        elif button == self.button_next and player_props.can_go_next:
            self.active_player.next()
        elif button == self.button_previous and player_props.can_go_previous:
            self.active_player.previous()
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
