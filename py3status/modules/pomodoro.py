# -*- coding: utf-8 -*-
"""
Pomodoro countdown on i3bar originally written by @Fandekasp (Adrien Lemaire)
"""

from subprocess import call
from time import time


class Py3status:

    # available configuration parameters
    max_breaks = 4
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

    @property
    def response(self):
        """
        Return the response full_text string
        """
        return {
            'full_text': '{} ({})'.format(self.prefix, self.timer)
        }

    def __setup(self, status):
        """
        Setup a step
        """
        self.status = status
        if status == 'stop':
            self.prefix = 'Pomodoro'
            self.status = 'stop'
            self.timer = self.timer_pomodoro
            self.breaks = 1

        elif status == 'start':
            self.prefix = 'Pomodoro'
            self.timer = self.timer_pomodoro

        elif status == 'break':
            self.prefix = 'Break #%d' % self.breaks
            if self.breaks > self.max_breaks:
                self.timer = self.timer_long_break
                self.breaks = 1
            else:
                self.breaks += 1
                self.timer = self.timer_break

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
        elif self.status == 'break':
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
