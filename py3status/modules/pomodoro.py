# -*- coding: utf-8 -*-
"""
Use Pomodoro technique to get things done easily.

Configuration parameters:
    button_advance: mouse button to advance the timer (default 3)
    button_reset: mouse button to reset the timer (default 2)
    button_toggle: mouse button to start/pause the timer (default 1)
    cache_timeout: refresh interval for this module, otherwise auto
        (default None)
    format: display format for this module
        *(default '[\?color=state [{progress_bar} ]{name} '
        '[\?if=name=Pomodoro {pomodoro} ][\?if=name=Break {break} ]'
        '[\?if=state ({time})|\[{time}\]]]')*
    format_notification: specify notification to format excluding colors
        (default 'End of {name}.')
    pomodoros: specify a number of pomodoros (intervals) (default 4)
    progress_bars: specify a number of bars or 3-tuples of numbers of
        bars for pomodoro, break, long break (default (0, 0, 0))
    sounds: specify a dict of sound file paths to play (default {})
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (1, 'good'), (2, 'degraded'), (3, 'orange')])
    timers: specify a number of seconds or 3-tuples of numbers of seconds
        for pomodoro, break, long break (default (1500, 300, 900))

Control placeholders:
    {alarm}          alarm boolean, eg False, True
    {started}        started boolean, eg False, True
    {state}          state number, eg 0, 1, 2, 3 for
                     stopped, pomodoro, break, long break

Format placeholders:
    {name}           name, eg Pomodoro, Break, Long Break
    {pomodoro}       pomodoro number, eg 3
    {break}          break number, eg 2
    {pomodoros}      total number of pomodoros, eg 4
    {progress}       progress percentage, eg 95
    {progress_bar}   progress bar, eg ◼◼◼◼◼◼◼◼◼◼
    {time}           time in [hh:]mm:ss, eg 8:16
    {time_hours}     time in hours, eg 0
    {time_minutes}   time in minutes, eg 8
    {time_seconds}   time in seconds, eg 16
    {total}          total time in [hh:]mm:ss, eg 24:1499
    {total_hours}    total time in hours, eg 0
    {total_minutes}  total time in minutes, eg 24
    {total_seconds}  total time in seconds, eg 1499
    {length}         length time in [hh:]mm:ss, eg 25:00
    {length_hours}   length time in hours, eg 0
    {length_minutes} length time in minutes, eg 25
    {length_seconds} length time in seconds, eg 00

Notes:
    We can also perform ceiling functions on time unit placeholders, eg
    `{placeholder:ceil}` to print `6` instead of `5.01`. You can find a
    format illustrating the differences between all four times in Examples
    below. You should only use `:ceil` on `{total_minutes}` placeholder.

    {total_hours:ceil}   ceil total time in hours, eg 1
    {total_minutes:ceil} ceil total time in minutes, eg 25
    {total_seconds:ceil} ceil total time in seconds, eg 1500

Format_notification placeholders:
    {name}      name, eg Pomodoro, Break, Long Break
    {pomodoro}  pomodoro number, eg 3
    {break}     break number, eg 2
    {pomodoros} total number of pomodoros, eg 4

Color options:
    color_bad:      Pomodoro/Break [stopped]
    color_degraded: Break [active]
    color_good:     Pomodoro/Break [active]

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Examples:
```
# specify a number or 3-tuples of numbers for progress_bars and timers
pomodoro {
    progress_bars = (5, 1, 3)     # pomodoro, break, long break
    progress_bars = 5             # 5 becomes (5, 5, 5)

    timers = (1500, 300, 900)     # pomodoro, break, long break
    timers = 300                  # 300 becomes (300, 300, 300)
}

# add sounds
pomodoro {
    sounds = {
        'pomodoro_start': '~/Music/Pomodoro_is_starting.mp3',
        'pomodoro_end': '~/Music/Pomodoro_is_ending.mp3',
        'break_start': '~/Music/Break_is_starting.mp3',
        'break_end': '~/Music/Break_is_ending.mp3',
        'long_break_start': '~/Music/Long_break_is_starting.mp3',
        'long_break_end': '~/Music/Long_break_is_ending.mp3',
    }
    # The songs for break* will also be playing for long_break* so we do
    # not have to specify same songs for long_break*... only when we want
    # to use different songs. You may also want to install ffplay.
}

# disable notifications, urgents
pomodoro {
    format_notification = ''
    allow_urgent = False

    # with urgent disabled, we can add "ALARM!" or an icon, eg...
    format = '[\?if=alarm&color=bad ALARM! ]'
        # OR
    format = '[\?if=alarm&color=gold \u23f0 {name}]'
}

# show notifications only on Pomodoro
pomodoro {
    format_notification = '\?if=name=Pomodoro You did '
    format_notification += '{pomodoro}/{pomodoros}.'
}

# our first pomodoro theme, make it look like a clock
pomodoro {
    format = '[\?color=state [{progress_bar} ]{time} ][\?max_length=1 {name}]'
    format += '[\?if=name=Pomodoro {pomodoro}|{break}]'
}

# monochrome theme
pomodoro {
    allow_urgent = False
    format_notification = ''
    progress_bars = 5
    thresholds = []
}

# rainbowize the legacy theme
pomodoro {
    format = '\?color=time_seconds [\?if=name=Pomodoro Pomodoro|Break #{break}] '
    format += '[\?if=state \[{total_seconds:ceil}\]|({total_seconds:ceil})]'
    format += '[ {progress_bar}]'

    format_notification = '[\?if=name=Pomodoro Pomodoro|[\?if=name=Break '
    format_notification += 'Break #{break}|Long Break]] time is up !'
    progress_bars = (25, 5, 15)

    thresholds = {
        'time_seconds': [
            (0, '#ffb3ba'), (10, '#ffdfba'), (20, '#ffffba'),
            (30, '#baffc9'), (40, '#bae1ff'), (50, '#bab3ff'),
        ],
    }
}

# minimal theme using total_minutes + ceil
pomodoro {
    format = '\?color=state [\?max_length=1 {name}]{total_minutes:ceil}'
}

# fewer cycles, less distracting, more relaxing
pomodoro {
    cache_timeout = 10
}

# show percent instead of running clock, more relaxing
pomodoro {
    format = '\?color=state [{progress_bar} ]{name} '
    format += '[\?if=name=Pomodoro {pomodoro} ][\?if=name=Break {break} ]'
    format += '[\?if=state ({progress}%)|\[{progress}%\]]'
}

# you can also use percent to accurately colorize the thresholds
pomodoro {
    format = '\?color=progress [{progress_bar} ]{name} '
    format += '[\?if=name=Pomodoro {pomodoro} ][\?if=name=Break {break} ]'
    format += '[\?if=state ({time})|\[{time}\]]'
    thresholds = [
        (100, 'darkgray'), (99, 'lightgreen'), (80, 'lime'),
        (60, 'orange'), (40,'degraded'), (20, 'bad')
    ]
    gradients = True  # show more colors
}

# show differences between time/length, total time, and ceil total time
pomodoro {
    format = 'Time: {time} ..... Length: {length} ..... Total Time: '
    format += '{total_hours}h, {total_minutes}m, {total_seconds}s'
    format += ' ..... Ceil Total Time: '
    format += '{total_hours:ceil}h, {total_minutes:ceil}m, {total_seconds:ceil}s'
    format_notification = ''
}

# display alarm bell icon instead of urgent, display PAUSED on paused
pomodoro {
    format = '[\?if=alarm&color=gold \u23f0 ]'
    format += '[\?if=state&color=state [{progress_bar} ]{time} ]'
    format += '[\?if=started [\?if=!state PAUSED ]]'
    format += '[\?max_length=1 {name}][\?if=name=Pomodoro {pomodoro}|{break}]'
    allow_urgent = False
}
```

@author Fandekasp (Adrien Lemaire), rixx, FedericoCeratto, schober-ch, ricci,
lasers

SAMPLE OUTPUT
[
    {'full_text': u'◼◼◼◼', 'color': '#FF0000'},
    {'full_text': u'◼ Pomodoro 1 [25:00]', 'color': '#FF0000'}
]

pomodoro
[
    {'full_text': u'◼', 'color': '#808080'},
    {'full_text': u'◼◼◼◼ Pomodoro 2 (19:59)', 'color': '#00FF00'}
]

break
[
    {'full_text': u'◼◼', 'color': '#808080'},
    {'full_text': u'◼◼◼ Break 3 (2:59)', 'color': '#FFFF00'}
]

long_break
[
    {'full_text': u'◼◼◼', 'color': '#808080'},
    {'full_text': u'◼◼ Long Break (5:59)', 'color': '#FFA500'}
]
"""

from threading import Timer
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    button_advance = 3
    button_reset = 2
    button_toggle = 1
    cache_timeout = None
    format = ('[\?color=state [{progress_bar} ]{name} '
              '[\?if=name=Pomodoro {pomodoro} ][\?if=name=Break {break} ]'
              '[\?if=state ({time})|\[{time}\]]]')
    format_notification = 'End of {name}.'
    pomodoros = 4
    progress_bars = (0, 0, 0)
    sounds = {}
    thresholds = [(0, 'bad'), (1, 'good'), (2, 'degraded'), (3, 'orange')]
    timers = (1500, 300, 900)  # 25min, 5min, 15min

    class Meta:
        def deprecate_sounds(config):
            return {
                'sounds': {
                    'break_end': config.get('sound_break_end'),
                    'pomodoro_end': config.get('sound_pomodoro_end'),
                    'pomodoro_start': config.get('sound_pomodoro_start'),
                }
            }

        def deprecate_timers(config):
            return {
                'timers': (
                    config.get('timer_pomodoro', 1500),
                    config.get('timer_break', 300),
                    config.get('timer_long_break', 900)
                ),
            }

        deprecated = {
            'function': [
                {'function': deprecate_sounds},
                {'function': deprecate_timers},
            ],
            'substitute_by_value': [
                {
                    'param': 'display_bar',
                    'value': False,
                    'substitute': {
                        'param': 'progress_bars',
                        'value': 0,
                    },
                    'msg': 'obsolete parameter: use {progress_bar}',
                },
                {
                    'param': 'display_bar',
                    'value': True,
                    'substitute': {
                        'param': 'progress_bars',
                        'value': 10,
                    },
                    'msg': 'obsolete parameter: use {progress_bar}',
                },
                {
                    'param': 'display_bar',
                    'value': True,
                    'substitute': {
                        'param': 'format',
                        'value': '\?show&color=state {progress_bar}'
                    },
                    'msg': 'obsolete parameter: use {progress_bar}',
                },
            ],
            'rename': [
                {
                    'param': 'max_breaks',
                    'new': 'pomodoros',
                    'msg': 'obsolete parameter use `pomodoros`',
                },
                {
                    'param': 'num_progress_bars',
                    'new': 'progress_bars',
                    'msg': 'obsolete parameter use `progress_bars`',
                },
            ],
            'remove': [
                {
                    'param': 'display_bar',
                    'msg': 'obsolete placeholder: use {progress_bar}',
                },
                {
                    'param': 'format_separator',
                    'msg': 'deprecated placeholder',
                },
            ],
            'rename_placeholder': [
                {
                    'placeholder': 'bar',
                    'new': 'progress_bar',
                    'format_strings': ['format'],
                },
                {
                    'placeholder': 'mm',
                    'new': 'total_minutes:ceil',
                    'format_strings': ['format'],
                },
                {
                    'placeholder': 'ss',
                    'new': 'total_seconds',
                    'format_strings': ['format'],
                },
                {
                    'placeholder': 'mmss',
                    'new': 'time',
                    'format_strings': ['format'],
                },
            ],
        }
        update_config = {
            'update_placeholder_format': [
                {
                    'placeholder_formats': {
                        'progress': ':.0f',
                        'time_hours': ':d',
                        'time_minutes': ':d',
                        'time_seconds': ':d',
                        'total_hours': ':d',
                        'total_minutes': ':d',
                        'total_seconds': ':d',
                        'length_hours': ':d',
                        'length_minutes': ':02d',
                        'length_seconds': ':02d',
                    },
                    'format_strings': ['format'],
                }
            ],
        }

    def post_config_hook(self):
        # support new, old (timers, progress_bars)
        for name in ['timers', 'progress_bars']:
            value = getattr(self, name)
            error_string = 'invalid ' + name
            if isinstance(value, tuple):
                if len(value) != 3:
                    raise Exception(error_string)
            elif isinstance(value, (list, str)):
                raise Exception(error_string)
            else:
                setattr(self, name, [value] * 3)

        # convert timers to dict
        self.name_list = ['Pomodoro', 'Break', 'Long Break']
        self.timers = dict(zip(self.name_list, self.timers))

        # support new, old sounds - drop the Nones first
        self.sounds = {k: v for k, v in self.sounds.items() if v}

        # set cache_timeout automagically
        if self.cache_timeout is None:
            self.cache_timeout = 10
            if any(x <= 60 for x in self.timers.values()):
                self.cache_timeout = 0
            time_periods = [
                ('*hours*', 3600), ('*minutes*', 60),
                ('*seconds*', 0), ('time', 0)
            ]
            for unit in time_periods:
                if self.py3.format_contains(self.format, unit[0]):
                    self.cache_timeout = unit[1]

        # init methods
        names = ['progress_bar', 'total', 'length']
        placeholders = ['progress_bar', 'total*', 'length*']
        self.init = {'methods': ['time'], 'thresholds': []}
        for name, placeholder in zip(names, placeholders):
            if self.py3.format_contains(self.format, placeholder):
                self.init['methods'].append(name)

        # init pomodoro
        self.init['methods'] = list(set(self.init['methods']))
        self._timer_reset()

        # init thresholds - partial future helper code
        for x in self.format.replace('&', ' ').split('color=')[1::1]:
            self.init['thresholds'].append(x.split()[0])
        self.init['thresholds'] = list(set(self.init['thresholds']))

    def _advance(self):
        if self.name == 'Pomodoro':
            self.name = 'Break'  # start break/long break soon
            self.break_count += 1
            if self.break_count >= self.pomodoros:
                self.name = 'Long Break'
        else:
            if self.name == 'Long Break':  # start pomodoro soon
                self.break_count = 0
            self.name = 'Pomodoro'
        self.time_left = self.timers[self.name]  # set new timer
        self.time_total = self.timers[self.name]
        self._is_running = False

    def _make_length(self, name, state, data, time):
        return self._make_time(name, state, data, self.time_total)

    def _make_total(self, name, state, data, time):
        return self._pack_time(name, data, (time / 3600), (time / 60), time)

    def _make_time(self, name, state, data, time):
        hours, remainder = divmod(time, 3600)
        minutes, seconds = divmod(remainder, 60)
        return self._pack_time(name, data, hours, minutes, seconds)

    def _pack_time(self, name, data, hours, minutes, seconds):
        if hours < 0:  # we print accurate, sometimes -1:59:59
            hours, minutes, seconds = (0, 0, 0)
        if int(hours):  # remove zero?
            data[name] = '%d:%02d:%02d' % (hours, minutes, seconds)
        else:
            data[name] = '%d:%02d' % (minutes, seconds)
        data[name + '_hours'] = hours
        data[name + '_minutes'] = minutes
        data[name + '_seconds'] = seconds
        return data

    def _make_progress_bar(self, name, state, data, time):
        bar = u''
        icon = u'\u25fc'
        width = self.progress_bars[self.name_list.index(self.name)]
        bar_time = time / self.time_total * width
        while bar_time > 0:
            bar += icon
            bar_time -= 1
        expired_bar = '[\?color=gray&show %s]' % icon * (width - len(bar))
        data['progress_bar'] = self.py3.safe_format(expired_bar + bar)
        return data

    def _make_sound(self, name):
        if self.sounds:
            if self.name in ['Pomodoro', 'Break']:
                name = '{}_{}'.format(self.name.lower(), name)
            else:
                for x in ['long_break', 'break']:
                    name = '{}_{}'.format(x, name)
                    if name in self.sounds:
                        break
            if name in self.sounds:
                self.py3.play_sound(self.sounds[name])

    def _timer_cancel(self):
        if self._timer:
            self._timer.cancel()
            self.py3.stop_sound()

    def _timer_end(self):
        self._make_sound('end')
        if self.format_notification:
            self.py3.notify_user(self.py3.safe_format(
                self.format_notification, {
                    'name': self.name,
                    'pomodoro': self.break_count + 1,
                    'break': self.break_count,
                    'pomodoros': self.pomodoros,
                }))
        self.alarm = True
        self._advance()
        self.py3.update()

    def _timer_reset(self):
        self.name = 'Pomodoro'
        self.alarm = False
        self.break_count = 0
        self.time_left = self.timers[self.name]
        self.time_total = self.timers[self.name]
        self._is_running = False
        self._end_time = None
        self._timer = None

    def pomodoro(self):
        if self._is_running:
            cached_until = self.cache_timeout
            state = self.name_list.index(self.name) + 1
            self.time_left = self._end_time - time()
        else:
            cached_until = self.py3.CACHE_FOREVER  # tobes, tyvm for this.
            state = 0  # stopped

        tomato_data = {
            'name': self.name,
            'state': state,
            'pomodoro': self.break_count + 1,
            'break': self.break_count,
            'pomodoros': self.pomodoros,
            'progress': self.time_left / self.time_total * 100.0,
            'started': self.time_left != self.timers[self.name],
            'alarm': self.alarm,
        }

        # make times and/or progress_bar
        for method_name in self.init['methods']:
            tomato_data = getattr(self, '_make_' + method_name)(
                method_name, state, tomato_data, self.time_left
            )

        # make thresholds
        for x in self.init['thresholds']:
            if x in tomato_data:
                self.py3.threshold_get_color(tomato_data[x], x)

        response = {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(self.format, tomato_data)
        }
        if self.alarm:
            response['urgent'] = True
            self.alarm = False
        return response

    def kill(self):
        self._timer_cancel()

    def on_click(self, event):
        button = event['button']
        buttons = [self.button_advance, self.button_reset, self.button_toggle]
        if button in buttons:
            self._timer_cancel()
        if button == self.button_toggle:
            if self._is_running:
                self.time_left = self._end_time - time()  # pause now
            else:
                self._end_time = time() + self.time_left  # start now
                self._timer = Timer(self.time_left, self._timer_end)
                self._timer.start()
                self._make_sound('start')
            self._is_running = not self._is_running  # toggle boolean
        elif button == self.button_reset:
            self._timer_reset()
        elif button == self.button_advance:
            self._advance()
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
