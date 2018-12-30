# -*- coding: utf-8 -*-
"""
Display song currently playing in moc.

MOC (music on console) is a console audio player for Linux/Unix designed to be
powerful and easy to use. It consists of two parts, a server (moc) and a
player/interface (mocp). It supports OGG, WAV, MP3 and other formats.

Configuration parameters:
    button_next: mouse button to skip next track (default None)
    button_pause: mouse button to pause/play the playback (default 1)
    button_previous: mouse button to skip previous track (default None)
    button_stop: mouse button to stop the playback (default 3)
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module
        *(default '\?if=is_started [\?if=is_stopped \[\] moc|'
        '[\?if=is_paused \|\|][\?if=is_playing >] {title}]')*
    sleep_timeout: when moc is not running, this interval will be used to
        allow one to refresh constantly with time placeholders and/or
        to refresh once every minute rather than every few seconds
        (default 20)

Control placeholders:
    {is_paused} a boolean based on moc status
    {is_playing} a boolean based on moc status
    {is_started} a boolean based on moc status
    {is_stopped} a boolean based on moc status

Format placeholders:
    {album} album name, eg (new output here)
    {artist} artist name, eg (new output here)
    {avgbitrate} audio average bitrate, eg 230kbps
    {bitrate} audio bitrate, eg 230kbps
    {currentsec} elapsed time in seconds, eg 32
    {currenttime} elapsed time in [HH:]MM:SS, eg 00:32
    {file} file location, eg /home/user/Music...
    {rate} audio rate, eg 44kHz
    {songtitle} song title, eg (new output here)
    {state} playback state, eg PLAY, PAUSE, STOP
    {timeleft} time left in [HH:]MM:SS, eg 71:30
    {title} track title, eg (new output here)
    {totalsec} total time in seconds, eg 4322
    {totaltime} total time in seconds, eg 72:02

    Placeholders are retrieved directly from `mocp --info` command.
    The list was harvested once and should not represent a full list.

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Stopped, defaults to color_bad

Requires:
    moc: a console audio player with simple ncurses interface

Examples:
```
# see 'man mocp' for more buttons
moc {
    on_click 9 = 'exec mocp --example'
}
```

@author lasers

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': '> Music For Programming - Mindaugaszq'}

paused
{'color': '#FFFF00', 'full_text': '|| Music For Programming - Mindaugaszq'}

stopped
{'color': '#FF0000', 'full_text': '[] moc'}
"""

from __future__ import division


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
        "\?if=is_started [\?if=is_stopped \[\] moc|"
        "[\?if=is_paused \|\|][\?if=is_playing >] {title}]"
    )
    sleep_timeout = 20

    def post_config_hook(self):
        if not self.py3.check_commands("mocp"):
            raise Exception(STRING_NOT_INSTALLED)

        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD

    def _get_moc_data(self):
        try:
            data = self.py3.command_output("mocp --info")
            is_started = True
        except self.py3.CommandError:
            data = {}
            is_started = False
        return is_started, data

    def moc(self):
        is_paused = is_playing = is_stopped = None
        cached_until = self.sleep_timeout
        color = self.py3.COLOR_BAD
        data = {}

        is_started, moc_data = self._get_moc_data()

        if is_started:
            cached_until = self.cache_timeout

            for line in moc_data.splitlines():
                category, value = line.split(": ", 1)
                data[category.lower()] = value

            self.state = data["state"]
            if self.state == "PLAY":
                is_playing = True
                color = self.color_playing
            elif self.state == "PAUSE":
                is_paused = True
                color = self.color_paused
            elif self.state == "STOP":
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
                    **data
                ),
            ),
        }

    def on_click(self, event):
        """
        Control moc with mouse clicks.
        """
        button = event["button"]
        if button == self.button_pause:
            if self.state == "STOP":
                self.py3.command_run("mocp --play")
            else:
                self.py3.command_run("mocp --toggle-pause")
        elif button == self.button_stop:
            self.py3.command_run("mocp --stop")
        elif button == self.button_next:
            self.py3.command_run("mocp --next")
        elif button == self.button_previous:
            self.py3.command_run("mocp --prev")
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
