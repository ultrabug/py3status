# -*- coding: utf-8 -*-
"""
Display song currently playing in Google Play Music Desktop Player.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module
        *(default '[\?if=is_started [\?if=title [\?if=playing&color=playing '
        '{title} - {artist}|\?color=paused (Paused) {title} - {artist}]|'
        '\?color=stopped Google Play Music]]')*
    sleep_timeout: sleep interval for this module (default 20)

Control placeholders:
    {is_started} a boolean based on pgrep data
    {playing} a boolean based on data status
    {rating_disliked} a boolean based on data status
    {rating_liked} a boolean based on data status

Format placeholders:
    {repeat} song repeat, eg NO_REPEAT, LIST_REPEAT, SINGLE_REPEAT
    {shuffle} song shuffle, eg NO_SHUFFLE, ALL_SHUFFLE
    {songLyrics} song lyrics, eg (whole lotta lyrics)
    {song_albumArt} album art url
    {song_album} album name
    {song_artist} artist name
    {song_title}  title name
    {time_currenttime} current time in [HH:]MM:SS
    {time_current} current time in milliseconds
    {time_totaltime} total time in [HH:]MM:SS
    {time_total} total time in milliseconds
    {volume} volume percent

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Not playing, defaults to color_bad

Requires:
    gpmdp: A beautiful cross platform Desktop Player for Google Play Music

@author Aaron Fields https://twitter.com/spirotot, lasers
@license BSD

SAMPLE OUTPUT
{'color': '#00ff00', 'full_text': 'The Show Goes On by Lupe Fiasco'}

paused
{'color': '#ffff00', 'full_text': '(Paused) The Show Goes On by Lupe Fiasco'}

stopped
{'color': '#ff0000', 'full_text': 'Google Play Music'}
"""

from __future__ import division
import json
import os

GPMDP = '~/.config/Google Play Music Desktop Player/json_store/playback.json'
PGREP = ['pgrep', '-f', 'Google Play Music Desktop Player']


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = ('[\?if=is_started [\?if=title [\?if=playing&color=playing '
              '{title} - {artist}|\?color=paused (Paused) {title} - {artist}]|'
              '\?color=stopped Google Play Music]]')
    sleep_timeout = 20

    def post_config_hook(self):
        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
        self.playback_json = os.path.expanduser(GPMDP)
        # DEPRECATION
        current = self.py3.format_contains(self.format, 'current')
        status = self.py3.format_contains(self.format, 'status')
        info = self.py3.format_contains(self.format, 'info')
        if current or status or info:
            msg = 'DEPRECATION WARNING: you are using old style configuration'
            msg += ' parameters you should update to use the new format.'
            self.py3.log(msg)

    def _is_running(self):
        try:
            self.py3.command_output(PGREP)
            return True
        except:
            return False

    def _ms_to_time(self, value):
        s, ms = divmod(value, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        time = '%d:%02d:%02d' % (h, m, s)
        return time.lstrip('0').lstrip(':')

    def _manipulate(self, data):
        temporary = {}
        for key, value in data.items():
            # milliseconds to [hh:]mm:ss
            if 'time_' in key:
                new_key = '%s%s' % (key, 'time')
                temporary[new_key] = self._ms_to_time(value)
                temporary[key] = value
            # DEPRECATION: compatible w/ gpmdp-remote's placeholders
            elif 'song_' in key:
                if 'albumArt' in key:
                    new_key = 'album_art'
                else:
                    new_key = key.replace('song_', '')
                temporary[new_key] = value
                temporary[key] = value
            else:
                temporary[key] = value

        # DEPRECATION: compatible w/ gpmdp-remote's status
        if data['playing']:
            status = temporary['status'] = 'Playing'
        else:
            status = temporary['status'] = 'Paused'
        # DEPRECATION: compatible w/ gpmdp-remote's current and info
        artist = data['song_artist']
        title = data['song_title']
        temporary['current'] = '%s - %s' % (artist, title)
        temporary['info'] = 'Now %s: %s by %s' % (status, title, artist)

        return temporary

    def gpmdp(self):
        data = {}
        is_started = None
        cached_until = self.sleep_timeout

        if self._is_running():
            cached_until = self.cache_timeout
            is_started = True
            with open(self.playback_json, 'r') as f:
                data = self.py3.flatten_dict(json.load(f), '_')
                data = self._manipulate(data)

        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(
                self.format, dict(is_started=is_started, **data))}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
