# -*- coding: utf-8 -*-
"""
Display and control a Pomodoro countdown.

Configuration parameters:
    - display_bar: display time in bars when True, otherwise in seconds
    - format: define custom display format. See placeholders below
    - max_breaks: maximum number of breaks
    - num_progress_bars: number of progress bars
    - sound_break_end: break end sound (file path) (requires pyglet
      or pygame)
    - sound_pomodoro_end: pomodoro end sound (file path) (requires pyglet
      or pygame)
    - sound_pomodoro_start: pomodoro start sound (file path) (requires pyglet
      od pygame)
    - timer_break: normal break time (seconds)
    - timer_long_break: long break time (seconds)
    - timer_pomodoro: pomodoro time (seconds)

Format of status string placeholders:
    {bar} - display time in bars
    {ss} - display time in total seconds (1500)
    {mm} - display time in total minutes (25)
    {mmss} - display time in (hh-)mm-ss (25:00)

i3status.conf example:

pomodoro {
    format = "{mmss} {bar}"
}

@author Fandekasp (Adrien Lemaire)
@author rixx
@author FedericoCeratto
@author schober-ch
"""

from subprocess import call
from syslog import syslog, LOG_INFO
from time import time
import datetime
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

# PROGRESS_BAR_ITEMS = u"▁▃▄▅▆▇█"
PROGRESS_BAR_ITEMS = u"▏▎▍▌▋▊▉"


class Py3status:
    """
    """
    # available configuration parameters
    display_bar = False
    format = u'{ss}'
    max_breaks = 4
    num_progress_bars = 5
    sound_break_end = None
    sound_pomodoro_end = None
    sound_pomodoro_start = None
    timer_break = 5 * 60
    timer_long_break = 15 * 60
    timer_pomodoro = 25 * 60

    def __init__(self):
        self.__setup('stop')
        self.alert = False
        self.run = False
        self.__player = Player()

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Handles click events:
            - left click starts an inactive counter and pauses a running
              Pomodoro
            - middle click resets everything
            - right click starts (and ends, if needed) a break

        """
        if event['button'] == 1:
            if self.status == 'stop':
                self.status = 'start'
                self.__play_sound(self.sound_pomodoro_start)
                self.run = True

            elif self.status == 'break':
                self.run = True

            elif self.status == 'start':
                if self.run:
                    self.status = 'pause'
                    self.run = False
                else:
                    self.run = True

            elif self.status == 'pause':
                self.status = 'start'
                self.run = True

        elif event['button'] == 2:
            self.__setup('stop')
            self.run = False

        elif event['button'] == 3:
            if self.status == 'break':
                self.__setup('start')
            else:
                self.__setup('break')
            self.run = False

    def _setup_mmss_time(self, form=None):
        """
        Setup the formatted time string.
        """
        time = str(datetime.timedelta(seconds=self.timer))
        components = time.split(':')

        if time[0] == '0':
            time = ':'.join(components[1:])
            if form == 'mm':
                time = components[-2]
        else:
            if form == 'mm':
                time = int(components[0]) * 60 + int(components[-2])

        return time

    def _setup_bar(self):
        """
        Setup the process bar.
        """
        bar = u''
        items_cnt = len(PROGRESS_BAR_ITEMS)
        bar = u''
        bar_val = float(self.timer) / self.time_window * \
            self.num_progress_bars
        while bar_val > 0:
            selector = int(bar_val * items_cnt)
            selector = min(selector, items_cnt - 1)
            bar += PROGRESS_BAR_ITEMS[selector]
            bar_val -= 1

        bar = bar.ljust(self.num_progress_bars)
        return bar

    @property
    def response(self):
        """
        Return the response full_text string
        """
        formatters = {
            'bar': self._setup_bar(),
            'ss': self.timer,
            'mm': self._setup_mmss_time(form='mm'),
            'mmss': self._setup_mmss_time()
        }

        if self.display_bar is True:
            self.format = u'{bar}'

        self.format = u'{}'.format(self.format)
        bar = self.format.format(**formatters)

        if self.run:
            text = u'{} [{}]'.format(self.prefix, bar)
        else:
            text = u'{} ({})'.format(self.prefix, bar)

        return dict(full_text=text)

    def __setup(self, status):
        """
        Setup a step
        """
        self.status = status
        if status == 'stop':
            self.prefix = 'Pomodoro'
            self.status = 'stop'
            self.timer = self.timer_pomodoro
            self.time_window = self.timer
            self.breaks = 1

        elif status == 'start':
            self.prefix = 'Pomodoro'
            self.timer = self.timer_pomodoro
            self.time_window = self.timer

        elif status == 'break':
            self.prefix = 'Break #%d' % self.breaks
            if self.breaks > self.max_breaks:
                self.timer = self.timer_long_break
                self.time_window = self.timer
                self.breaks = 1
            else:
                self.breaks += 1
                self.timer = self.timer_break
                self.time_window = self.timer

    def __decrement(self):
        """
        Countdown handler
        """
        self.timer -= 1
        if self.timer < 0:
            self.alert = True
            self.run = False
            if self.status == 'start':
                self.__play_sound(self.sound_pomodoro_end)

            elif self.status == 'break':
                self.__play_sound(self.sound_break_end)

            self.__i3_nagbar()

            if self.status == 'start':
                self.__setup('break')
                self.status = 'break'

            elif self.status == 'break':
                self.__setup('start')
                self.status = 'start'

    def __i3_nagbar(self, level='warning'):
        """
        Make use of i3-nagbar to display warnings to the user.
        """
        msg = '{} time is up !'.format(self.prefix)
        try:
            call(['i3-nagbar', '-m', msg, '-t', level],
                 stdout=open('/dev/null', 'w'),
                 stderr=open('/dev/null', 'w'))
        except:
            pass

    def pomodoro(self, i3s_output_list, i3s_config):
        """
        Pomodoro response handling and countdown
        """
        if self.run:
            self.__decrement()

        response = self.response
        if self.alert:
            response['urgent'] = True
            self.alert = False

        if self.status == 'start':
            response['color'] = i3s_config['color_good']
        elif self.status == 'break':
            response['color'] = i3s_config['color_degraded']
        else:
            response['color'] = i3s_config['color_bad']

        response['cached_until'] = time()
        return response

    def __play_sound(self, sound_fname):
        """Play sound if required
        """
        if not sound_fname:
            return

        if not self.__player.available:
            syslog(LOG_INFO, "pomodoro module: the pyglet or pygame "
                   "library are required to play sounds")
            return

        try:
            self.__player(sound_fname)
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
