# -*- coding: utf-8 -*-
"""
Display songs currently playing in DeaDBeeF.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module (default '[{artist} - ][{title}]')
    sleep_timeout: when deadbeef is not running, this interval will be used
        to allow faster refreshes with time-related placeholders and/or
        to refresh few times per minute rather than every few seconds
        (default 20)

Format placeholders:
    {album} name of the album
    {artist} name of the artist
    {length} length time in [HH:]MM:SS
    {playback_time} elapsed time in [HH:]MM:SS
    {title} title of the track
    {tracknumber} track number in two digits
    {year} year in four digits

    For more placeholders, see title formatting 2.0 in 'deadbeef --help'
    or https://github.com/DeaDBeeF-Player/deadbeef/wiki/Title-formatting-2.0
    Not all of Foobar2000 remapped metadata fields will work with deadbeef and
    a quick reminder about using {placeholders} here instead of %placeholder%.

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Stopped, defaults to color_bad

Requires:
    deadbeef: a GTK+ audio player for GNU/Linux

Examples:
```
# see 'deadbeef --help' for more buttons
deadbeef {
    on_click 1 = 'exec deadbeef --play-pause'
    on_click 8 = 'exec deadbeef --random'
}
```

@author mrt-prodz

SAMPLE OUTPUT
{'color': '#00ff00', 'full_text': 'Music For Programming - Lackluster'}

paused
{'color': '#ffff00', 'full_text': 'Music For Programming - Lackluster'}
"""

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = "[{artist} - ][{title}]"
    sleep_timeout = 20

    class Meta:
        deprecated = {
            "remove": [{"param": "delimiter", "msg": "obsolete parameter"}],
            "rename_placeholder": [
                {
                    "placeholder": "elapsed",
                    "new": "playback_time",
                    "format_strings": ["format"],
                },
                {
                    "placeholder": "tracknum",
                    "new": "tracknumber",
                    "format_strings": ["format"],
                },
            ],
        }

    def post_config_hook(self):
        if not self.py3.check_commands("deadbeef"):
            raise Exception(STRING_NOT_INSTALLED)

        self.separator = "|SEPARATOR|"
        self.placeholders = list(
            set(self.py3.get_placeholders_list(self.format) + ["isplaying"])
        )
        self.deadbeef_command = 'deadbeef --nowplaying-tf "{}"'.format(
            self.separator.join(["%{}%".format(x) for x in self.placeholders])
        )
        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD

    def _is_running(self):
        try:
            self.py3.command_output(["pgrep", "deadbeef"])
            return True
        except self.py3.CommandError:
            return False

    def _get_deadbeef_data(self):
        # Deadbeef can generate lot of startup noises with or without error
        # codes. Running command sometimes change how things behaves onscreen
        # too. We used subprocess in the past to ignore error codes. We also
        # use pgrep and hidden placeholders to dictate how status output and
        # color should look... mainly to stay consistency in multiple versions
        # (e.g., Python2.7 to Python3+ and nonstop deadbeef-git commits).
        try:
            return self.py3.command_output(self.deadbeef_command)
        except self.py3.CommandError as ce:
            return ce.output

    def deadbeef(self):
        beef_data = {}
        cached_until = self.sleep_timeout
        color = self.color_stopped

        if self._is_running():
            line = self._get_deadbeef_data()
            beef_data = dict(zip(self.placeholders, line.split(self.separator)))
            cached_until = self.cache_timeout

            if beef_data["isplaying"]:
                color = self.color_playing
            else:
                color = self.color_paused

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, beef_data),
            "color": color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
