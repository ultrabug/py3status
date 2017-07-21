# -*- coding: utf-8 -*-
"""
Display song currently playing in Google Play Music Desktop Player.

Configuration parameters:
    cache_timeout: refresh and sleep interval for this module (default [5, 20])
    format: display format for this module
        (default '[\?if=is_playing {title} - {artist}]
        [\?if=is_paused [(Paused) {title} - {artist}]]
        [\?if=is_stopped Google Play Music]')

Control placeholders:
    is_paused: a boolean based on gpmdp status
    is_playing: a boolean based on gpmdp status
    is_started: a boolean based on gpmdp status
    is_stopped: a boolean based on gpmdp status
    ----------
    playing: a boolean based on song status
    rating_disliked: a boolean based on rating status
    rating_liked: a boolean based on rating status

Format placeholders:
    {time_current_hms} current time in [HH:]MM:SS
    {time_total_hms} total time in [HH:]MM:SS
    ----------
    {album_art} URL to album art
    {album} album name
    {artist} artist name
    {repeat} repeat eg LIST_REPEAT, SINGLE_REPEAT, or NO_REPEAT
    {shuffle} shuffle eg ALL_SHUFFLE or NO_SHUFFLE
    {songLyrics} lyrics (100~ lines)
    {time_current} current time in milliseconds
    {time_total} total time in milliseconds
    {title}  title name
    {volume} volume number

Color options:
    color_paused: Paused, defaults to color_degraded
    color_playing: Playing, defaults to color_good
    color_stopped: Not playing, defaults to color_bad

Requires:
    gpmdp: A beautiful cross platform Desktop Player for Google Play Music

Examples:
```
# same thing in slim version
gpmdp {
    format = '\?if=is_started [\?if=is_stopped Google Play Music|' +\
             '[\?if=is_paused (Paused)] {title} - {artist}]'
}
```

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


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = [5, 20]
    format = '\?if=is_started [\?if=is_stopped Google Play Music|' +\
             '[\?if=is_paused (Paused)] {title} - {artist}]'

    def post_config_hook(self):
        self.color_paused = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
        self.color_playing = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
        self.color_stopped = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD

        self.playback_json = os.path.expanduser(GPMDP)
        if isinstance(self.cache_timeout, int):
            self.cache_timeout = [self.cache_timeout, self.cache_timeout]

        # DEPRECATION WARNING
        current = self.py3.format_contains(self.format, 'current')
        status = self.py3.format_contains(self.format, 'status')
        info = self.py3.format_contains(self.format, 'info')
        if current or status or info:
            msg = 'DEPRECATION WARNING: you are using old style configuration'
            msg += ' parameters you should update to use the new format.'
            self.py3.log(msg)

    def _is_running(self):
        try:
            cmd = ['pgrep', '-f', 'Google Play Music Desktop Player']
            self.py3.command_output(cmd)
            return True
        except:
            return False

    def _ms_to_time(self, value):
        s, ms = divmod(value, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        time = '%d:%02d:%02d' % (h, m, s)
        return time.lstrip('0').lstrip(':')

    def _manipulate_data(self, data):
        temporary = {}
        for key, value in data.items():
            # milliseconds to [hh:]mm:ss
            if 'time_' in key:
                new_key = '%s%s' % (key, '_hms')
                temporary[new_key] = self._ms_to_time(value)
                temporary[key] = value
            # compatible w/ gpmdp-remote's placeholders
            elif 'song_' in key:
                if 'albumArt' in key:
                    new_key = 'album_art'
                else:
                    new_key = key.replace('song_', '')
                temporary[new_key] = value
            else:
                temporary[key] = value

        # compatible w/ gpmdp-remote's status
        if data['playing']:
            status = temporary['status'] = 'Playing'
        else:
            status = temporary['status'] = 'Paused'

        # compatible w/ gpmdp-remote's current and info
        artist = data['song_artist']
        title = data['song_title']
        temporary['current'] = '%s - %s' % (artist, title)
        temporary['info'] = 'Now %s: %s by %s' % (status, title, artist)

        return temporary

    def gpmdp(self):
        data = {}
        color = self.py3.COLOR_BAD
        is_paused = is_playing = is_started = is_stopped = None
        cached_until = self.cache_timeout[1]

        if self._is_running():
            cached_until = self.cache_timeout[0]
            is_started = True

            with open(self.playback_json, 'r') as f:
                data = self.py3.flatten_dict(json.load(f), '_')
                data = self._manipulate_data(data)

            if data['time_total'] == 0:
                color = self.color_stopped
                is_stopped = True
            elif data['playing']:
                color = self.color_playing
                is_playing = True
            else:
                color = self.color_paused
                is_paused = True

        return {
            'cached_until': self.py3.time_in(cached_until),
            'color': color,
            'full_text': self.py3.safe_format(self.format,
                                              dict(
                                                  is_paused=is_paused,
                                                  is_playing=is_playing,
                                                  is_started=is_started,
                                                  is_stopped=is_stopped,
                                                  **data
                                              ))
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
