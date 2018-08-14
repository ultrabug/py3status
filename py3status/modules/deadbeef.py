# -*- coding: utf-8 -*-
"""
Display song currently playing in deadbeef.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module (default '[{artist} - ][{title}]')
    sleep_timeout: when deadbeef is not running, this interval will be used
        to allow one to refresh constantly with time placeholders and/or
        to refresh once every minute rather than every few seconds
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
    or http://github.com/Alexey-Yakovenko/deadbeef/wiki/Title-formatting-2.0
    Not all of Foobar2000 remapped metadata fields will work with deadbeef and
    a quick reminder about using {placeholders} here instead of %placeholder%.

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Stopped, defaults to color_bad

Requires:
    deadbeef: a GTK+ audio player for GNU/Linux

@author mrt-prodz, tobes, lasers

SAMPLE OUTPUT
{'color': '#00ff00', 'full_text': 'Music For Programming - Lackluster'}

paused
{'color': '#ffff00', 'full_text': 'Music For Programming - Lackluster'}
"""

from subprocess import check_output

FMT_PARAMETER = ['isplaying']
FMT_SEPARATOR = u'\u001e'
STRING_NOT_INSTALLED = 'not installed'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = '[{artist} - ][{title}]'
    sleep_timeout = 20

    class Meta:
        deprecated = {
            'remove': [
                {
                    'param': 'delimiter',
                    'msg': 'obsolete parameter',
                },
            ],
            'rename_placeholder': [
                {
                    'placeholder': 'elapsed',
                    'new': 'playback_time',
                    'format_strings': ['format'],
                },
                {
                    'placeholder': 'tracknum',
                    'new': 'tracknumber',
                    'format_strings': ['format'],
                },
            ],
        }

    def post_config_hook(self):
        if not self.py3.check_commands('deadbeef'):
            raise Exception(STRING_NOT_INSTALLED)
        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD

        # mix format and necessary placeholders with separator...
        # then we merge together to run deadbeef command only once
        self.placeholders = list(
            set(self.py3.get_placeholders_list(self.format)) |
            set(FMT_PARAMETER))
        self.empty_status = {x: '' for x in self.placeholders}
        fmt = FMT_SEPARATOR.join(['%{}%'.format(x) for x in self.placeholders])
        self.cmd = 'deadbeef --nowplaying-tf "%s"' % fmt

    def _is_running(self):
        try:
            self.py3.command_output(['pgrep', 'deadbeef'])
            return True
        except:
            return False

    def deadbeef(self):
        color = self.color_stopped
        status = self.empty_status
        cached_until = self.sleep_timeout

        if self._is_running():
            cached_until = self.cache_timeout
            # Starting deadbeef may generate lot of startup noises either
            # with or without error codes. Running command below may sometimes
            # change how things behaves onscreen. We use subprocess to ignore
            # error codes. We use pgrep and hidden placeholders to dictate
            # how status output and color should look... mainly to stay
            # consistency between versions.
            out = check_output(self.cmd, shell=True).decode('utf-8')

            # We know 7.0 and 7.1 returns a literal 'nothing' string.
            # Deadbeef stopped doing that in 7.2 so we adds a quick check
            # here to skip status if it contains 'nothing' or FMT_SEPARATOR.
            if out not in ['nothing', FMT_SEPARATOR]:

                # split placeholders results
                status = dict(zip(self.placeholders, out.split(FMT_SEPARATOR)))

                if status['isplaying'] == '1':
                    color = self.color_playing
                else:
                    color = self.color_paused
        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(self.format, status),
            'color': color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
