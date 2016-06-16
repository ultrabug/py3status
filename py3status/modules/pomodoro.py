# -*- coding: utf-8 -*-
"""
Display and control a Pomodoro countdown.

Configuration parameters:
    display_bar: display time in bars when True, otherwise in seconds
    format: define custom display format. See placeholders below
    format_separator: separator between minutes:seconds
    colors: a comma separated string of color values for each state,
        eg: "on=#FFFFFF, off=#FF0000, break=#FCE94F".
    max_breaks: maximum number of breaks
    num_progress_bars: number of progress bars
    sound_break_end: break end sound (file path) (requires pyglet
        or pygame)
    sound_pomodoro_end: pomodoro end sound (file path) (requires pyglet
        or pygame)
    sound_pomodoro_start: pomodoro start sound (file path) (requires pyglet
        od pygame)
    timer_break: normal break time (seconds)
    timer_long_break: long break time (seconds)
    timer_pomodoro: pomodoro time (seconds)

Format of status string placeholders:
    {bar} display time in bars
    {ss} display time in total seconds (1500)
    {mm} display time in total minutes (25)
    {mmss} display time in (hh-)mm-ss (25:00)

i3status.conf example:
```
pomodoro {
    format = "{mmss} {bar}"
}
```

@author Fandekasp (Adrien Lemaire), rixx, FedericoCeratto, schober-ch
"""

from math import ceil
from threading import Timer
from time import time
import os

try:
    from pygame import mixer as pygame_mixer
except ImportError:
    pygame_mixer = None

try:
    import pyglet
except ImportError:
    pyglet = None


class Player(object):
    _default = '_silence'

    def __init__(self):
        if pyglet is not None:
            pyglet.options['audio'] = ('pulse', 'silent')
            self._player = pyglet.media.Player()
            self._default = '_pyglet'
        elif pygame_mixer is not None:
            pygame_mixer.init()
            self._default = '_pygame'

    def _silence(self, sound_fname):
        pass

    def _pygame(self, sound_fname):
        pygame_mixer.music.load(sound_fname)
        pygame_mixer.music.play()

    def _pyglet(self, sound_fname):
        res_dir, f = os.path.split(sound_fname)

        if res_dir not in pyglet.resource.path:
            pyglet.resource.path = [res_dir]
            pyglet.resource.reindex()

        self._player.queue(pyglet.resource.media(f, streaming=False))
        self._player.play()

    @property
    def available(self):
        return self._default != '_silence'

    def __call__(self, sound_fname):
        getattr(self, self._default)(os.path.expanduser(sound_fname))

PROGRESS_BAR_ITEMS = u"▏▎▍▌▋▊▉"


class Py3status:
    """
    """
    # available configuration parameters
    display_bar = False
    format = u'{ss}'
    format_separator = u"-"
    max_breaks = 4
    num_progress_bars = 5
    sound_break_end = None
    sound_pomodoro_end = None
    sound_pomodoro_start = None
    timer_break = 5 * 60
    timer_long_break = 15 * 60
    timer_pomodoro = 25 * 60
    colors = None

    def __init__(self):
        self._initialized = False

    def _init(self):
        self._break_number = 0
        self._active = True
        self._running = False
        self._time_left = self.timer_pomodoro
        self._section_time = self.timer_pomodoro
        self._prefix = 'Pomodoro'
        self._timer = None
        self._end_time = None
        self._player = Player()
        self._format = 'Pomodoro {time}'
        self._alert = False
        if self.display_bar is True:
            self.format = u'{bar}'
        self._colors = dict()
        self._initialized = True

    def _time_up(self):
        self.py3.notify_user('{} time is up !'.format(self._prefix))
        self._alert = True
        self._advance()

    def _advance(self, user_action=False):
        self._running = False
        if self._active:
            if not user_action:
                self._play_sound(self.sound_pomodoro_end)
            # start break
            self._time_left = self.timer_break
            self._section_time = self.timer_break
            self._break_number += 1
            self._format = 'Break #{} {{time}}'.format(self._break_number)
            self._prefix = 'Break #{}'.format(self._break_number)
            if self._break_number > self.max_breaks:
                self._time_left = self.timer_long_break
                self._section_time = self.timer_long_break
                self._break_number = 0
            self._active = False
        else:
            if not user_action:
                self._play_sound(self.sound_break_end)
            self._time_left = self.timer_pomodoro
            self._section_time = self.timer_pomodoro
            self._format = 'Pomodoro {time}'
            self._prefix = 'Pomodoro'
            self._active = True

    def kill(self):
        '''
        cancel any timer
        '''
        if self._timer:
            self._timer.cancel()

    def on_click(self, event):
        """
        Handles click events:
            - left click starts an inactive counter and pauses a running
              Pomodoro
            - middle click resets everything
            - right click starts (and ends, if needed) a break
        """
        if event['button'] == 1:
            if self._running:
                self._running = False
                self._time_left = self._end_time - time()
                if self._timer:
                    self._timer.cancel()
            else:
                self._running = True
                self._end_time = time() + self._time_left
                if self._timer:
                    self._timer.cancel()
                self._timer = Timer(self._time_left, self._time_up)
                self._timer.start()
                if self._active:
                    self._play_sound(self.sound_pomodoro_start)

        elif event['button'] == 2:
            # reset
            self._init()
            if self._timer:
                self._timer.cancel()

        elif event['button'] == 3:
            # advance
            self._advance(user_action=True)
            if self._timer:
                self._timer.cancel()

    def _setup_bar(self):
        """
        Setup the process bar.
        """
        bar = u''
        items_cnt = len(PROGRESS_BAR_ITEMS)
        bar_val = float(self._time_left) / self._section_time * \
            self.num_progress_bars
        while bar_val > 0:
            selector = int(bar_val * items_cnt)
            selector = min(selector, items_cnt - 1)
            bar += PROGRESS_BAR_ITEMS[selector]
            bar_val -= 1

        bar = bar.ljust(self.num_progress_bars)
        return bar

    def pomodoro(self, i3s_output_list, i3s_config):
        """
        Pomodoro response handling and countdown
        """
        if not self._initialized:
            self._init()

        cached_until = 0
        if self._running:
            self._time_left = ceil(self._end_time - time())
            time_left = ceil(self._time_left)
        else:
            time_left = ceil(self._time_left)

        vals = {
            'ss': int(time_left),
            'mm': int(ceil(time_left / 60)),
        }

        if '{mmss}' in self.format:
            hours, rest = divmod(time_left, 3600)
            mins, seconds = divmod(rest, 60)

            if hours:
                vals['mmss'] = u'%d%s%02d%s%02d' % (hours,
                                                    self.format_separator,
                                                    mins,
                                                    self.format_separator,
                                                    seconds)
            else:
                vals['mmss'] = u'%d%s%02d' % (mins,
                                              self.format_separator,
                                              seconds)

        if '{bar}' in self.format:
            vals['bar'] = self._setup_bar()

        if self._running:
            format = u'{{prefix}} [{}]'.format(self.format)
        else:
            format = u'{{prefix}} ({})'.format(self.format)
            cached_until = self.py3.CACHE_FOREVER

        response = {
            'full_text': format.format(prefix=self._prefix, **vals),
            'cached_until': cached_until,
        }

        if self._alert:
            response['urgent'] = True
            self._alert = False

        if self.colors:
            try:
                self._colors = dict((k.strip(), v.strip()) for k, v in (
                    color.split('=') for color in self.colors.split(',')))
            except:
                self.py3.log("pomodoro module: colors parsing error")
                self._colors = dict()

        if not self._running:
            response['color'] = self._colors.get('off') or i3s_config['color_bad']
        else:
            if self._active:
                response['color'] = self._colors.get('on') or i3s_config['color_good']
            else:
                response['color'] = self._colors.get('break') or i3s_config['color_degraded']

        return response

    def _play_sound(self, sound_fname):
        """Play sound if required
        """
        if not sound_fname:
            return

        if not self._player.available:
            self.py3.log("pomodoro module: the pyglet or pygame "
                         "library are required to play sounds")
            return

        try:
            self._player(sound_fname)
        except Exception:
            return


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.pomodoro([], config))
        sleep(1)
