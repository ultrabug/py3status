"""
Control Audacious or VLC media player.

Provides an icon to control simple functions of audio/video players:
    - start (left click)
    - stop  (left click)
    - pause (middle click)

Configuration parameters:
    cache_timeout: how often to update in seconds (default 10)
    debug: enable verbose logging (bool) (default False)
    format: format of the output (default "{icon}")
    pause_icon: (default '❚❚')
    play_icon: (default '▶')
    stop_icon: (default '◼')
    supported_players: supported players (str) (comma separated list)
        (default 'audacious,vlc')
    volume_tick: percentage volume change on mouse wheel (int) (positive number
        or None to disable it) (default 1)

Format placeholders:
    {icon} an icon to control music/video players

@author Federico Ceratto <federico.ceratto@gmail.com>, rixx
@license BSD

SAMPLE OUTPUT
{'full_text': u'\u25b6'}

stop
{'full_text': u'\u25fc'}

pause
{'full_text': u'\u275a\u275a'}
"""
# Any contributor to this module should add his/her name to the @author
# line, comma separated.

from pathlib import Path

try:
    import dbus

    dbus_available = True
except:  # noqa e722 // (ImportError, ModuleNotFoundError):  # (py2, assumed py3)
    dbus_available = False


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    debug = False
    format = "{icon}"
    pause_icon = "❚❚"
    play_icon = "▶"
    stop_icon = "◼"
    supported_players = "audacious,vlc"
    volume_tick = 1

    def post_config_hook(self):
        self.status = "stop"
        self.icon = self.play_icon

    def on_click(self, event):
        """
        """
        buttons = (None, "left", "middle", "right", "up", "down")
        try:
            button = buttons[event["button"]]
        except IndexError:
            return

        if button in ("up", "down"):
            if self.volume_tick is None:
                return

            self._change_volume(button == "up")
            return

        if self.status == "play":
            if button == "left":
                self._stop()

            elif button == "middle":
                self._pause()

        elif self.status == "stop":
            if button == "left":
                self._play()

        elif self.status == "pause":
            if button in ("left", "right"):
                self._play()

    def _run(self, command):
        if self.debug:
            self.py3.log(f"running {command}")
        self.py3.command_run(command)

    def _play(self):
        self.status = "play"
        self.icon = self.stop_icon
        player_name = self._detect_running_player()
        if player_name == "audacious":
            self._run(["audacious", "-p"])
        elif player_name == "vlc":
            player = self._get_vlc()
            if player:
                player.Play()

    def _stop(self):
        self.status = "stop"
        self.icon = self.play_icon
        player_name = self._detect_running_player()
        if player_name == "audacious":
            self._run(["audacious", "-s"])
        elif player_name == "vlc":
            player = self._get_vlc()
            if player:
                player.Stop()

    def _pause(self):
        self.status = "pause"
        self.icon = self.pause_icon
        player_name = self._detect_running_player()
        if player_name == "audacious":
            self._run(["audacious", "-u"])
        elif player_name == "vlc":
            player = self._get_vlc()
            if player:
                player.Pause()

    def _change_volume(self, increase):
        """Change volume using amixer
        """
        sign = "+" if increase else "-"
        delta = f"{self.volume_tick}%{sign}"
        self._run(["amixer", "-q", "sset", "Master", delta])

    def _detect_running_player(self):
        """Detect running player process, if any
        """
        supported_players = self.supported_players.split(",")
        running_players = []
        for pid in Path("/proc").iterdir():
            if not pid.name.isdigit():
                continue
            try:
                player_name = (pid / "comm").read_bytes().decode().rstrip()
            except:  # noqa e722
                # (IOError, FileNotFoundError):  # (assumed py2, assumed py3)
                continue

            if player_name in supported_players:
                running_players.append(player_name)

        # Pick which player to use based on the order in self.supported_players
        for player_name in supported_players:
            if player_name in running_players:
                if self.debug:
                    self.py3.log(f"found player: {player_name}")

                # those players need the dbus module
                if player_name == "vlc" and not dbus_available:
                    self.py3.log(f"{player_name} requires the dbus python module")
                    return None

                return player_name

        return None

    def _get_vlc(self):
        mpris = "org.mpris.MediaPlayer2"
        mpris_slash = "/" + mpris.replace(".", "/")
        bus = dbus.SessionBus()
        proxy = bus.get_object(mpris + ".vlc", mpris_slash)
        return dbus.Interface(proxy, dbus_interface=mpris + ".Player")

    def player_control(self):
        return dict(
            full_text=self.py3.safe_format(self.format, {"icon": self.icon}),
            cached_until=self.py3.time_in(self.cache_timeout),
        )


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
