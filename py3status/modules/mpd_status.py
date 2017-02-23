# coding: utf-8
"""
Display song currently playing in mpd.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 2)
    format: template string (see below)
        (default '%state% [[[%artist%] - %title%]|[%file%]]')
    hide_when_paused: hide the status if state is paused (default False)
    hide_when_stopped: hide the status if state is stopped (default True)
    host: mpd host (default 'localhost')
    max_width: maximum status length (default 120)
    password: mpd password (default None)
    port: mpd port (default '6600')
    state_pause: label to display for "paused" state (default '[pause]')
    state_play: label to display for "playing" state (default '[play]')
    state_stop: label to display for "stopped" state (default '[stop]')

Color options:
    color_pause: Paused, default color_degraded
    color_play: Playing, default color_good
    color_stop: Stopped, default color_bad

Requires:
    python-mpd2: (NOT python2-mpd2)
```
# pip install python-mpd2
```

Refer to the mpc(1) manual page for the list of available placeholders to be
used in `format`.
You can also use the %state% placeholder, that will be replaced with the state
label (play, pause or stop).
Every placeholder can also be prefixed with `next_` to retrieve the data for
the song following the one currently playing.

You can also use {} instead of %% for placeholders (backward compatibility).

Examples of `format`
```
# Show state and (artist -) title, if no title fallback to file:
%state% [[[%artist% - ]%title%]|[%file%]]

# Alternative legacy syntax:
{state} [[[{artist} - ]{title}]|[{file}]]

# Show state, [duration], title (or file) and next song title (or file):
%state% \[%time%\] [%title%|%file%] → [%next_title%|%next_file%]
```

@author shadowprince, zopieux
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': '[play] Music For Programming - Idol Eyes'}
"""

import ast
import datetime
import itertools
import socket
from mpd import MPDClient, CommandError


def parse_template(instr, value_getter, found=True):
    """
    MPC-like parsing of `instr` using `value_getter` callable to retrieve the
    text representation of placeholders.
    """
    instr = iter(instr)
    ret = []
    for char in instr:
        if char in '%{':
            endchar = '%' if char == '%' else '}'
            key = ''.join(itertools.takewhile(lambda e: e != endchar, instr))
            value = value_getter(key)
            if value:
                found = True
                ret.append(value)
            else:
                found = False
        elif char == '#':
            ret.append(next(instr, '#'))
        elif char == '\\':
            ln = next(instr, '\\')
            if ln in 'abtnvfr':
                ret.append(ast.literal_eval('"\\{}"'.format(ln)))
            else:
                ret.append(ln)
        elif char == '[':
            subret, found = parse_template(instr, value_getter, found)
            subret = ''.join(subret)
            ret.append(subret)
        elif char == ']':
            if found:
                ret = ''.join(ret)
                return ret, True
            else:
                return '', False
        elif char == '|':
            subret, subfound = parse_template(instr, value_getter, found)
            if found:
                pass
            elif subfound:
                ret.append(''.join(subret))
                found = True
            else:
                return '', False
        elif char == '&':
            subret, subfound = parse_template(instr, value_getter, found)
            if found and subfound:
                subret = ''.join(subret)
                ret.append(subret)
            else:
                return '', False
        else:
            ret.append(char)

    ret = ''.join(ret)
    return ret, found


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
    format = '%state% [[[%artist%] - %title%]|[%file%]]'
    hide_when_paused = False
    hide_when_stopped = True
    host = 'localhost'
    max_width = 120
    password = None
    port = '6600'
    state_pause = '[pause]'
    state_play = '[play]'
    state_stop = '[stop]'

    def _state_character(self, state):
        if state == 'play':
            return self.state_play
        elif state == 'pause':
            return self.state_pause
        elif state == 'stop':
            return self.state_stop
        return '?'

    def current_track(self):
        try:
            c = MPDClient()
            c.connect(host=self.host, port=self.port)
            if self.password:
                c.password(self.password)

            status = c.status()
            song = int(status.get('song', 0))
            next_song = int(status.get('nextsong', 0))

            state = status.get('state')

            if ((state == 'pause' and self.hide_when_paused) or
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

                song['state'] = next_song['state'] \
                              = self._state_character(state)

                def attr_getter(attr):
                    if attr.startswith('next_'):
                        return song_attr(next_song, attr[5:])
                    return song_attr(song, attr)

                text, _ = parse_template(self.format, attr_getter)

        except socket.error:
            text = "Failed to connect to mpd!"
            state = None
        except CommandError:
            text = "Failed to authenticate to mpd!"
            state = None
            c.disconnect()
        else:
            c.disconnect()

        if len(text) > self.max_width:
            text = u'{}...'.format(text[:self.max_width - 3])

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': text,
        }

        if state:
            if state == 'play':
                response['color'] = self.py3.COLOR_PLAY or self.py3.COLOR_GOOD
            elif state == 'pause':
                response['color'] = (self.py3.COLOR_PAUSE or
                                     self.py3.COLOR_DEGRADED)
            elif state == 'stop':
                response['color'] = self.py3.COLOR_STOP or self.py3.COLOR_BAD

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
