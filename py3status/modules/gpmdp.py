# -*- coding: utf-8 -*-
"""
Display song currently playing in Google Play Music Desktop Player.

Configuration parameters:
    cache_timeout:  refresh interval for this module (default 5)
    format:         display format for this module (default '♫[ {status}]')
    state_paused:   show this when gpmdp paused playback
        (default '[(Paused) {song_title} - {song_artist}]')
    state_playing:  show this when gpmdp started playback
        (default '{song_title} - {song_artist}')

Format placeholders:
    {status}          Google Play Music Desktop Player status

State placeholders:
    {songLyrics}      Print song lyrics
    {song_album}      Print song album
    {song_artist}     Print song artist
    {song_title}      Print song title
    {time_current}    Print time (current) in milliseconds
    {time_total}      Print time (total) in milliseconds

    Placeholders are retrieved directly from keys/values in JSON playback file.
    We found more placeholders from the file although these may not be useful for
    some percent of users. We're keeping them here for everybody's convenience.

    {playing}         Print boolean
    {volume}          Print number
    {shuffle}         Print value, eg NO_SHUFFLE
    {repeat}          Print value, eg NO_REPEAT
    {song_albumArt}   Print long URL to song album art
    {rating_disliked} Print boolean
    {rating_liked}    Print boolean

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Not playing, defaults to color_bad

Requires:
    gpmdp: A beautiful cross platform Desktop Player for Google Play Music
           See http://www.googleplaymusicdesktopplayer.com/

@author Aaron Fields https://twitter.com/spirotot, lasers
@license BSD

SAMPLE OUTPUT
{'full_text': '♫ Now Playing: The Show Goes On by Lupe Fiasco'}
"""

import json
import os

GPMDP = "~/.config/Google Play Music Desktop Player/json_store/playback.json"


def flatten_dict(d, delimiter='_'):
    def expand(key, value):
        if isinstance(value, dict):
            return [
                (delimiter.join([key, k]), v)
                for k, v in flatten_dict(value, delimiter).items()
            ]
        else:
            return [(key, value)]
    return dict([item for k, v in d.items() for item in expand(k, v)])


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = u'♫[ {status}]'
    state_paused = '[(Paused) {song_title} - {song_artist}]'
    state_playing = '{song_title} - {song_artist}'

    class Meta:
        deprecated = {
            'remove': [
                {
                    'param': 'current',
                    'msg': 'obsolete set. use new parameters'
                },
                {
                    'param': 'info',
                    'msg': 'obsolete set. use new parameters'
                },
            ],
        }

    def post_config_hook(self):
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
        self.playback_json = os.path.expanduser(GPMDP)

    def _is_running(self):
        try:
            cmd = ['pgrep', '-f', 'Google Play Music Desktop Player']
            self.py3.command_run(cmd)
            return True
        except:
            return False

    def gpmdp(self):
        if not self._is_running():
            return {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format),
                'color': self.color_stopped
            }
        data = []
        with open(self.playback_json, 'r') as f:
            data = json.load(f, object_hook=flatten_dict)

        if data['playing']:
            color = self.color_playing
            status = self.py3.safe_format(self.state_playing, data)
        else:
            color = self.color_paused
            status = self.py3.safe_format(self.state_paused, data)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'status': status}),
            'color': color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
