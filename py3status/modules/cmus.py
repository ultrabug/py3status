r"""
Display song currently playing in cmus.

cmus (C* Music Player) is a small, fast and powerful console audio player
which supports most major audio formats. Various features include gapless
playback, ReplayGain support, MP3 and Ogg streaming, live filtering, instant
startup, customizable key-bindings, and vi-style default key-bindings.

Configuration parameters:
    button_next: mouse button to skip next track (default None)
    button_pause: mouse button to pause/play the playback (default 1)
    button_previous: mouse button to skip previous track (default None)
    button_stop: mouse button to stop the playback (default 3)
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module
        *(default '[\?if=is_started [\?if=is_playing > ][\?if=is_paused \|\| ]'
        '[\?if=is_stopped .. ][[{artist}][\?soft  - ][{title}]'
        '|\?show cmus: waiting for user input]]')*
    sleep_timeout: sleep interval for this module. when cmus is not running,
        this interval will be used. this allows some flexible timing where one
        might want to refresh constantly with some placeholders... or to refresh
        only once every minute rather than every few seconds. (default 20)

Control placeholders:
    {is_paused} a boolean based on cmus status
    {is_playing} a boolean based on cmus status
    {is_started} a boolean based on cmus status
    {is_stopped} a boolean based on cmus status
    {continue} a boolean based on data status
    {play_library} a boolean based on data status
    {play_sorted} a boolean based on data status
    {repeat} a boolean based on data status
    {repeat_current} a boolean based on data status
    {replaygain} a boolean based on data status
    {replaygain_limit} a boolean based on data status
    {shuffle} a boolean based on data status
    {softvol} a boolean based on data status
    {stream} a boolean based on data status

Format placeholders:
    {aaa_mode} shuffle mode, eg artist, album, all
    {albumartist} album artist, eg (new output here)
    {album} album name, eg (new output here)
    {artist} artist name, eg (new output here)
    {bitrate} audio bitrate, eg 229
    {comment} comment, eg URL
    {date} year number, eg 2015
    {duration} length time in seconds, eg 171
    {durationtime} length time in [HH:]MM:SS, eg 02:51
    {file} file location, eg /home/user/Music...
    {position} elapsed time in seconds, eg 17
    {positiontime} elapsed time in [HH:]MM:SS, eg 00:17
    {replaygain_preamp} replay gain preamp, eg 0.000000
    {status} playback status, eg playing, paused, stopped
    {title} track title, eg (new output here)
    {tracknumber} track number, eg 0
    {vol_left} left volume number, eg 90
    {vol_right} right volume number, eg 90

    Placeholders are retrieved directly from `cmus-remote --query` command.
    The list was harvested only once and should not represent a full list.

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Stopped, defaults to color_bad

Requires:
    cmus: a small feature-rich ncurses-based music player

@author lasers

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': '> Music For Programming - Big War'}

paused
{'color': '#FFFF00', 'full_text': '|| Music For Programming - Big War'}

stopped
{'color': '#FF0000', 'full_text': '.. Music For Programming - Big War'}

waiting
{'color': '#FF0000', 'full_text': '.. cmus: waiting for user input'}
"""


STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    button_next = None
    button_pause = 1
    button_previous = None
    button_stop = 3
    cache_timeout = 5
    format = (
        r"[\?if=is_started [\?if=is_playing > ][\?if=is_paused \|\| ]"
        r"[\?if=is_stopped .. ][[{artist}][\?soft  - ][{title}]"
        r"|\?show cmus: waiting for user input]]"
    )
    sleep_timeout = 20

    def post_config_hook(self):
        if not self.py3.check_commands("cmus-remote"):
            raise Exception(STRING_NOT_INSTALLED)

        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD

    def _seconds_to_time(self, value):
        m, s = divmod(int(value), 60)
        h, m = divmod(m, 60)
        time = f"{h}:{m:02d}:{s:02d}"
        return time.lstrip("0").lstrip(":")

    def _get_cmus_data(self):
        try:
            data = self.py3.command_output(["cmus-remote", "--query"])
            is_started = True
        except self.py3.CommandError:
            data = {}
            is_started = False
        return is_started, data

    def _organize_data(self, data):
        temporary = {}
        for line in data.splitlines():
            category, _, value = line.partition(" ")
            if category in ("set", "tag"):
                key, _, value = value.partition(" ")
                temporary[key] = value
            else:
                temporary[category] = value
        return temporary

    def _manipulate_data(self, data):
        temporary = {}
        for key, value in data.items():
            # seconds to time
            if key in ("duration", "position"):
                new_key = "{}{}".format(key, "time")
                temporary[new_key] = self._seconds_to_time(value)
                temporary[key] = value
            # values to boolean
            elif value in ("true", "enabled"):
                temporary[key] = True
            elif value in ("false", "disabled"):
                temporary[key] = False
            # string not modified
            else:
                temporary[key] = value

        # stream to boolean
        if "stream" in data:
            temporary["stream"] = True

        return temporary

    def cmus(self):
        """
        """
        is_paused = is_playing = is_stopped = None
        cached_until = self.sleep_timeout
        color = self.py3.COLOR_BAD

        is_started, data = self._get_cmus_data()

        if is_started:
            cached_until = self.cache_timeout
            data = self._organize_data(data)
            data = self._manipulate_data(data)

            status = data.get("status")
            if status == "playing":
                is_playing = True
                color = self.color_playing
            elif status == "paused":
                is_paused = True
                color = self.color_paused
            elif status == "stopped":
                is_stopped = True
                color = self.color_stopped

        return {
            "cached_until": self.py3.time_in(cached_until),
            "color": color,
            "full_text": self.py3.safe_format(
                self.format,
                dict(
                    is_paused=is_paused,
                    is_playing=is_playing,
                    is_started=is_started,
                    is_stopped=is_stopped,
                    **data,
                ),
            ),
        }

    def on_click(self, event):
        """
        Control cmus with mouse clicks.
        """
        button = event["button"]
        if button == self.button_pause:
            self.py3.command_run("cmus-remote --pause")
        elif button == self.button_stop:
            self.py3.command_run("cmus-remote --stop")
        elif button == self.button_next:
            self.py3.command_run("cmus-remote --next")
        elif button == self.button_previous:
            self.py3.command_run("cmus-remote --prev")
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
