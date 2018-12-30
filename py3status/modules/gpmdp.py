# -*- coding: utf-8 -*-
"""
Display song currently playing in Google Play Music Desktop Player.

Configuration parameters:
    cache_timeout:  refresh interval for this module (default 5)
    format:         specify the items and ordering of the data in the status bar.
                    These area 1:1 match to gpmdp-remote's options
                    (default '♫ {info}')

Format placeholders:
    {info}            Print info about now playing song
    {title}           Print current song title
    {artist}          Print current song artist
    {album}           Print current song album
    {album_art}       Print current song album art URL
    {time_current}    Print current song time in milliseconds
    {time_total}      Print total song time in milliseconds
    {status}          Print whether GPMDP is paused or playing
    {current}         Print now playing song in "artist - song" format


Requires:
    gpmdp: https://www.googleplaymusicdesktopplayer.com/
    gpmdp-remote: https://github.com/iandrewt/gpmdp-remote

@author Aaron Fields https://twitter.com/spirotot
@license BSD

SAMPLE OUTPUT
{'full_text': '♫ Now Playing: The Show Goes On by Lupe Fiasco'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = u"♫ {info}"

    def gpmdp(self):
        def _run_cmd(cmd):
            return self.py3.command_output(["gpmdp-remote", cmd]).strip()

        full_text = ""
        if _run_cmd("status") == "Playing":
            cmds = [
                "info",
                "title",
                "artist",
                "album",
                "status",
                "current",
                "time_total",
                "time_current",
                "album_art",
            ]
            data = {}
            for cmd in cmds:
                if self.py3.format_contains(self.format, "{0}".format(cmd)):
                    data[cmd] = _run_cmd(cmd)
            full_text = self.py3.safe_format(self.format, data)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
