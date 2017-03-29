# -*- coding: utf-8 -*-
"""
Display song currently playing in mpd.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 2)
    format: template string (see below)
        (default '{state} [[[{artist}] - {title}]|[{file}]]')
    hide_when_paused: hide the status if state is paused (default False)
    hide_when_stopped: hide the status if state is stopped (default True)
    hide_when_playing: hide the status if state is playing (default False)
    host: mpd host (default 'localhost')
    max_width: maximum status length (default 120)
    mpd_no_auth: show this when mpd authentication failed
        (default 'mpd: authentication failed')
    mpd_no_conn: show this when mpd connection refused
        (default 'mpd: connection refused')
    password: mpd password (default None)
    port: mpd port (default '6600')
    state_pause: show this when mpd paused playback (default '[pause]')
    state_play: show this when mpd started playback (default '[play]')
    state_stop: show this when mpd stopped playback (default '[stop]')

Color options:
    color_pause: Paused, defaults to color_degraded
    color_play: Playing, defaults to color_good
    color_stop: Stopped, defaults to color_bad

Format placeholders:
    {state} state (paused, playing. stopped) can be defined via `state_..`
        configuration parameters
    Refer to the mpc(1) manual page for the list of available placeholders to
    be used in the format.  Placeholders should use braces `{}` rather than
    percent `%%` eg `{artist}`.
    Every placeholder can also be prefixed with
    `next_` to retrieve the data for the song following the one currently
    playing.

Requires:
    python-mpd2: (NOT python2-mpd2)
```
# pip install python-mpd2
```

Note: previously formats using %field% where allowed for this module, but
standard placeholders should be used.

Examples of `format`
```
# Show state and (artist -) title, if no title fallback to file:
{state} [[[{artist} - ]{title}]|[{file}]]

# Show state, [duration], title (or file) and next song title (or file):
{state} \[{time}\] [{title}|{file}] → [{next_title}|{next_file}]
```

@author shadowprince, zopieux
@license Eclipse Public License

SAMPLE OUTPUT
{'color': '#00ff00', 'full_text': '[play] Music For Programming - Idol Eyes'}

paused
{'color': '#ffff00', 'full_text': '[pause] Music For Programming - Idol Eyes'}

stopped
{'color': '#ff0000', 'full_text': '[stop] Music For Programming - Idol Eyes'}
"""

import datetime
import re
import socket
from mpd import MPDClient, CommandError


def song_attr(song, attr):
    def parse_mtime(date_str):
        return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')

    if attr == 'time':
        try:
            duration = int(song['time'])
            if duration > 0:
                minutes, seconds = divmod(duration, 60)
                return '{:d}:{:02d}'.format(minutes, seconds)
            raise ValueError
        except (KeyError, ValueError):
            return ''
    elif attr == 'position':
        try:
            return '{}'.format(int(song['pos']) + 1)
        except (KeyError, ValueError):
            return ''
    elif attr == 'mtime':
        return parse_mtime(song['last-modified']).strftime('%c')
    elif attr == 'mdate':
        return parse_mtime(song['last-modified']).strftime('%x')

    return song.get(attr, '')


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 2
    format = '{state} [[[{artist}] - {title}]|[{file}]]'
    hide_when_paused = False
    hide_when_playing = False
    hide_when_stopped = True
    host = 'localhost'
    max_width = 120
    mpd_no_auth = 'mpd: authentication failed'
    mpd_no_conn = 'mpd: connection refused'
    password = None
    port = '6600'
    state_pause = '[pause]'
    state_play = '[play]'
    state_stop = '[stop]'

    def post_config_hook(self):
        # Convert from %placeholder% to {placeholder}
        # This is not perfect but should be good enough
        if not self.py3.get_placeholders_list(self.format) and '%' in self.format:
            self.format = re.sub('%([a-z]+)%', r'{\1}', self.format)
            self.py3.log('Old % style format DEPRECATED use { style format')

        # Assign colors
        self.color_pause = self.py3.COLOR_PAUSE or self.py3.COLOR_DEGRADED
        self.color_play = self.py3.COLOR_PLAY or self.py3.COLOR_GOOD
        self.color_stop = self.py3.COLOR_STOP or self.py3.COLOR_BAD

    def _get_state(self, state):
        if state == 'play':
            return self.state_play
        elif state == 'pause':
            return self.state_pause
        elif state == 'stop':
            return self.state_stop
        return '?'

    def current_track(self):
        try:
            state = None
            c = MPDClient()
            c.connect(host=self.host, port=self.port)
            if self.password:
                c.password(self.password)

            status = c.status()
            song = int(status.get('song', 0))
            next_song = int(status.get('nextsong', 0))
            state = status.get('state')

            if ((state == 'pause' and self.hide_when_paused) or
                    (state == 'play' and self.hide_when_playing) or
                    (state == 'stop' and self.hide_when_stopped)):
                text = ''

            else:
                playlist_info = c.playlistinfo()
                try:
                    song = playlist_info[song]
                except IndexError:
                    song = {}
                try:
                    next_song = playlist_info[next_song]
                except IndexError:
                    next_song = {}

                song['state'] = next_song['state'] = self._get_state(state)

                def attr_getter(attr):
                    if attr.startswith('next_'):
                        return song_attr(next_song, attr[5:])
                    return song_attr(song, attr)

                text = self.py3.safe_format(self.format, attr_getter=attr_getter)

        except socket.error:
            text = self.py3.safe_format(self.mpd_no_conn)
        except CommandError:
            text = self.py3.safe_format(self.mpd_no_auth)
            c.disconnect()
        else:
            c.disconnect()

        if len(text) > self.max_width:
            text = u'{}...'.format(text[:self.max_width - 3])

        if state == 'play':
            color = self.color_play
        elif state == 'pause':
            color = self.color_pause
        else:
            color = self.color_stop

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': text,
            'color': color
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
