# -*- coding: utf-8 -*-
"""
Pomodoro countdown on i3bar originally written by @Fandekasp (Adrien Lemaire)
"""

from subprocess import call
from time import time

# PROGRESS_BAR_ITEMS = u"▁▃▄▅▆▇█"
PROGRESS_BAR_ITEMS = u"▏▎▍▌▋▊▉"


class Py3status:
    """
    Configuration parameters:
        - display_bar: display time in bars when True, otherwise in seconds
        - max_breaks: maximum number of breaks
        - num_progress_bars: number of progress bars
        - timer_break: normal break time (seconds)
        - timer_long_break: long break time (seconds)
        - timer_pomodoro: pomodoro time (seconds)
    """

    # available configuration parameters
    display_bar = False
    max_breaks = 4
    num_progress_bars = 5
    timer_break = 5 * 60
    timer_long_break = 15 * 60
    timer_pomodoro = 25 * 60

    def __init__(self):
        self.__setup('stop')
        self.alert = False
        self.run = False

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Handles click events
        """
        if event['button'] == 1:
            if self.status == 'stop':
                self.status = 'start'
            self.run = True

        elif event['button'] == 2:
            self.__setup('stop')
            self.run = False

        elif event['button'] == 3:
            self.__setup('pause')
            self.run = False

    @property
    def response(self):
        """
        Return the response full_text string
        """
        if self.display_bar and self.status in ('start', 'pause'):
            bar = u''
            items_cnt = len(PROGRESS_BAR_ITEMS)
            bar = u''
            bar_val = float(self.timer) / self.time_window * self.num_progress_bars
            while bar_val > 0:
                selector = int(bar_val * items_cnt)
                selector = min(selector, items_cnt - 1)
                bar += PROGRESS_BAR_ITEMS[selector]
                bar_val -= 1

            bar = bar.ljust(self.num_progress_bars).encode('utf_8')
        else:
            bar = self.timer

        if self.run:
            text = '{} [{}]'.format(self.prefix, bar)
        else:
            text = '{} ({})'.format(self.prefix, bar)

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

        elif status == 'pause':
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
            self.__i3_nagbar()
            if self.status == 'start':
                self.__setup('pause')
                self.status = 'pause'
            elif self.status == 'pause':
                self.__setup('start')
                self.status = 'start'

    def __i3_nagbar(self, level='warning'):
        """
        Make use of i3-nagbar to display warnings to the user.
        """
        msg = '{} time is up !'.format(self.prefix)
        try:
            call(
                ['i3-nagbar', '-m', msg, '-t', level],
                stdout=open('/dev/null', 'w'),
                stderr=open('/dev/null', 'w')
            )
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
        elif self.status == 'pause':
            response['color'] = i3s_config['color_degraded']
        else:
            response['color'] = i3s_config['color_bad']

        response['cached_until'] = time()
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.pomodoro([], config))
        sleep(1)
