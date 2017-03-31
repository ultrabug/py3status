# -*- coding: utf-8 -*-
"""
Display song currently playing in deadbeef.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    delimiter: delimiter between metadata fields (default 'ÐÉÅÐƁÊËF')
    format: display format for this module (default '[{artist} - ][{title}]')

Format placeholders:
    {artist} Name of the artist of the track.
    {isplaying} "1" if file is currently playing, empty string otherwise.
    {length} The length of the track formatted as hours, minutes,
                and seconds, rounded to the nearest second.
    {playback_time} The elapsed time formatted as [HH:]MM:SS.
    {title} Title of the track.
    {tracknumber} Two-digit index of specified track within the album.
    {year} Year formatted as four digits from a time/date string.

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Stopped, defaults to color_bad

Requires:
    deadbeef: a GTK+ audio player for GNU/Linux

@author mrt-prodz
"""

import subprocess


class Py3status:
    # available configuration parameters
    cache_timeout = 1
    delimiter = u'ÐÉÅÐƁÊËF'
    format = '[{artist} - ][{title}]'

    class Meta:
        deprecated = {
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

    def _is_running(self):
        try:
            self.py3.command_output(['pgrep', 'deadbeef'])
            return True
        except:
            return False

    def deadbeef(self):
        color = self.color_stopped
        artist = isplaying = length = playback_time = title = \
            tracknumber = year = ""

        if not self._is_running():
            return {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'color': color,
                'full_text': ''
            }

        # mix metadata fields in with the delimiters
        fmt = self.delimiter.join([
            '%artist%', '%isplaying%', '%length%', '%playback_time%',
            '%title%', '%tracknumber%', '%year%'
        ])
        # Starting deadbeef may generate lot of startup noises either with
        # or without error codes. Running deadbeef command below may sometimes
        # change how things behaves onscreen. We use subprocess to ignore error
        # codes and using pgrep to control how status output and color will
        # look... mainly to build consistency better between versions.

        # run command and get output
        out = subprocess.check_output(['deadbeef', '--nowplaying-tf', fmt])
        out = out.decode('utf-8')

        # get metadata results out of the string using the delimiters
        if out != 'nothing':
            artist, isplaying, length, playback_time, title, tracknumber, \
                year = out.split(self.delimiter)
            # color
            if title:
                if isplaying == "1":
                    color = self.color_playing
                else:
                    color = self.color_paused
        # response
        deadbeef = self.py3.safe_format(self.format,
                                        dict(
                                            artist=artist,
                                            isplaying=isplaying,
                                            length=length,
                                            playback_time=playback_time,
                                            title=title,
                                            tracknumber=tracknumber,
                                            year=year
                                        ))
        return {
            'color': color,
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': deadbeef
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
