# -*- coding: utf-8 -*-
"""
Display song currently playing in deadbeef.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    delimiter: delimiter between metadata fields (default '¥å¥å¥å')
    format: display format for this module (default '{artist} - {title}')

Format placeholders:
    {artist}        artist
    {length}        length
    {playback_time} playback time
    {title}         title
    {tracknumber}   track number
    {year}          year

Color options:
    color_degraded: Paused
    color_good: Playing
    color_bad: Not Playing

Requires:
    deadbeef: a GTK+ audio player for GNU/Linux

@author mrt-prodz
"""

import subprocess


class Py3status:
    # available configuration parameters
    cache_timeout = 1
    delimiter = u'¥å¥å¥å'
    format = '{artist} - {title}'

    class Meta:
        deprecated = {
            'rename_placeholder': [
                {
                    'placeholder': 'elapsed',
                    'new': 'playback_time',
                    'format_strings': ['format'],
                },
            ],
        }

    def _is_running(self):
        try:
            self.py3.command_output(['pgrep', 'deadbeef'])
            return True
        except:
            return False

    def deadbeef(self):
        color = self.py3.COLOR_BAD
        artist = isplaying = length = playback_time = title = \
            tracknumber = year = ""

        if not self._is_running():
            return {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'color': color,
                'full_text': '',
            }

        # mix metadata fields in with the delimiters
        fmt = self.delimiter.join([
            '%artist%', '%isplaying%', '%length%', '%playback_time%',
            '%title%', '%tracknumber%', '%year%'
        ])
        # run command and get output
        out = subprocess.check_output(['deadbeef', '--nowplaying-tf', fmt])
        out = out.decode('utf-8')

        # get metadata results out of the string using the delimiters
        if out != 'nothing':
            artist, isplaying, length, playback_time, title, tracknumber, \
                year = out.split(self.delimiter)

            if title:
                if isplaying == "1":
                    color = self.py3.COLOR_GOOD
                else:
                    color = self.py3.COLOR_DEGRADED

        # response
        deadbeef = self.py3.safe_format(self.format, dict(
            artist=artist, isplaying=isplaying, length=length,
            playback_time=playback_time, title=title,
            tracknumber=tracknumber, year=year))

        deadbeef = deadbeef.strip().strip('-').strip(':')

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
