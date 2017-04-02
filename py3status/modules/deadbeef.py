# -*- coding: utf-8 -*-
"""
Display song currently playing in deadbeef.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    format: display format for this module (default '[{artist} - ][{title}]')

Format placeholders:
    {album} name of the album
    {artist} name of the artist
    {length} length time in [HH:]MM:SS
    {playback_time} elapsed time in [HH:]MM:SS
    {title} title of the track
    {tracknumber} track number in two digits
    {year} year in four digits

    For more placeholders, see new title formatting in 'deadbeef --help'
    or http://github.com/Alexey-Yakovenko/deadbeef/wiki/Title-formatting-2.0
    Not all of Foobar2000 remapped metadata fields will work in deadbeef.

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Stopped, defaults to color_bad

Requires:
    deadbeef: a GTK+ audio player for GNU/Linux

SAMPLE OUTPUT
{'full_text': 'Music For Programming - Lackluster'}

@author mrt-prodz, tobes, lasers
"""

from subprocess import check_output

CONTROL_PARAMETERS = ['%title%', '%isplaying%']
CONTROL_SEPARATOR = u''
FORMAT_SEPARATOR = u''


class Py3status:
    # available configuration parameters
    cache_timeout = 1
    format = '[{artist} - ][{title}]'

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
        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
        self.placeholders = self.py3.get_placeholders_list(self.format)

    def _is_running(self):
        try:
            self.py3.command_output(['pgrep', 'deadbeef'])
            return True
        except:
            return False

    def deadbeef(self):
        color = self.color_stopped
        status = ''

        if not self._is_running():
            return {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format),
                'color': color
            }

        # merge format placeholders with format separators
        # merge hidden placeholders with control separators
        # merge strings together to run deadbeef command only once
        out = FORMAT_SEPARATOR.join(['%{}%'.format(x) for x in self.placeholders])
        control = [CONTROL_SEPARATOR + s for s in (CONTROL_PARAMETERS)]
        fmt = ''.join(out) + ''.join(control)

        # Starting deadbeef may generate lot of startup noises either with
        # or without error codes. Running deadbeef command below may sometimes
        # change how things behaves onscreen. We use subprocess to ignore error
        # codes and using pgrep to control how status output and color will
        # look... mainly to build consistency better between versions.
        out = check_output('deadbeef --nowplaying-tf "%s"' % fmt, shell=True)
        out = out.decode('utf-8')

        # 7.1 backward compatible
        if out != 'nothing':

            # split control results
            # split placeholders results
            out, title, isplaying = out.split(CONTROL_SEPARATOR)
            status = dict(zip(self.placeholders, out.split(FORMAT_SEPARATOR)))

            # 7.0 backward compatible, I think
            if title:
                if isplaying == "1":
                    color = self.color_playing
                else:
                    color = self.color_paused
        return {
            'color': color,
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, status)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
