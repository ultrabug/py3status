"""
Use Pomodoro technique to get things done easily.

Button 1 starts/pauses countdown.
Button 2 switch Pomodoro/Break.
Button 3 resets timer.

Configuration parameters:
    display_bar: display time in bars when True, otherwise in seconds
        (default False)
    format: define custom time format. See placeholders below (default '{ss}')
    format_active: format to display when timer is active
        (default 'Pomodoro [{format}]')
    format_break: format to display during break
        (default 'Break #{breakno} [{format}]')
    format_break_stopped: format to display during a break that is stopped
        (default 'Break #{breakno} ({format})')
    format_separator: separator between minutes:seconds (default ':')
    format_stopped: format to display when timer is stopped
        (default 'Pomodoro ({format})')
    num_progress_bars: number of progress bars (default 5)
    pomodoros: specify a number of pomodoros (intervals) (default 4)
    sound_break_end: break end sound (file path) (requires pyglet
        or pygame) (default None)
    sound_pomodoro_end: pomodoro end sound (file path) (requires pyglet
        or pygame) (default None)
    sound_pomodoro_start: pomodoro start sound (file path) (requires pyglet
        or pygame) (default None)
    timer_break: normal break time (seconds) (default 300)
    timer_long_break: long break time (seconds) (default 900)
    timer_pomodoro: pomodoro time (seconds) (default 1500)

Format placeholders:
    {bar} display time in bars
    {breakno} current break number
    {ss} display time in total seconds (1500)
    {mm} display time in total minutes (25)
    {mmss} display time in (hh-)mm-ss (25:00)

Color options:
    color_bad: Pomodoro not running
    color_degraded: Pomodoro break
    color_good: Pomodoro active

Examples:
```
pomodoro {
    format = "{mmss} {bar}"
}
```

@author Fandekasp (Adrien Lemaire), rixx, FedericoCeratto, schober-ch, ricci

SAMPLE OUTPUT
{'color': '#FF0000', 'full_text': u'Pomodoro (1500)'}

running
{'color': '#00FF00', 'full_text': u'Pomodoro [1483]'}
"""

import time
from math import ceil
from threading import Timer


PROGRESS_BAR_ITEMS = "▏▎▍▌▋▊▉"


class Py3status:
    """
    """

    # available configuration parameters
    display_bar = False
    format = "{ss}"
    format_active = "Pomodoro [{format}]"
    format_break = "Break #{breakno} [{format}]"
    format_break_stopped = "Break #{breakno} ({format})"
    format_separator = ":"
    format_stopped = "Pomodoro ({format})"
    num_progress_bars = 5
    pomodoros = 4
    sound_break_end = None
    sound_pomodoro_end = None
    sound_pomodoro_start = None
    timer_break = 5 * 60
    timer_long_break = 15 * 60
    timer_pomodoro = 25 * 60

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "max_breaks",
                    "new": "pomodoros",
                    "msg": "obsolete parameter use `pomodoros`",
                }
            ]
        }

    def post_config_hook(self):
        self._initialized = False

    def _init(self):
        self._break_number = 0
        self._active = True
        self._running = False
        self._time_left = self.timer_pomodoro
        self._section_time = self.timer_pomodoro
        self._timer = None
        self._end_time = None
        self._alert = False
        if self.display_bar is True:
            self.format = "{bar}"
        self._initialized = True

    def _time_up(self):
        if self._active:
            self.py3.notify_user("Pomodoro time is up !")
        else:
            self.py3.notify_user(f"Break #{self._break_number} time is up !")
        self._alert = True
        self._advance()

    def _advance(self, user_action=False):
        self._running = False
        if self._active:
            if not user_action:
                self.py3.play_sound(self.sound_pomodoro_end)
            # start break
            self._time_left = self.timer_break
            self._section_time = self.timer_break
            self._break_number += 1
            if self._break_number >= self.pomodoros:
                self._time_left = self.timer_long_break
                self._section_time = self.timer_long_break
                self._break_number = 0
            self._active = False
        else:
            if not user_action:
                self.py3.play_sound(self.sound_break_end)
            self._time_left = self.timer_pomodoro
            self._section_time = self.timer_pomodoro
            self._active = True

    def kill(self):
        """
        cancel any timer
        """
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
        if event["button"] == 1:
            if self._running:
                self._running = False
                self._time_left = self._end_time - time.perf_counter()
                if self._timer:
                    self._timer.cancel()
            else:
                self._running = True
                self._end_time = time.perf_counter() + self._time_left
                if self._timer:
                    self._timer.cancel()
                self._timer = Timer(self._time_left, self._time_up)
                self._timer.start()
                if self._active:
                    self.py3.play_sound(self.sound_pomodoro_start)

        elif event["button"] == 2:
            # reset
            self._init()
            if self._timer:
                self._timer.cancel()

        elif event["button"] == 3:
            # advance
            self._advance(user_action=True)
            if self._timer:
                self._timer.cancel()

    def _setup_bar(self):
        """
        Setup the process bar.
        """
        bar = ""
        items_cnt = len(PROGRESS_BAR_ITEMS)
        bar_val = self._time_left / self._section_time * self.num_progress_bars
        while bar_val > 0:
            selector = min(int(bar_val * items_cnt), items_cnt - 1)
            bar += PROGRESS_BAR_ITEMS[selector]
            bar_val -= 1

        bar = bar.ljust(self.num_progress_bars)
        return bar

    def pomodoro(self):
        """
        Pomodoro response handling and countdown
        """
        if not self._initialized:
            self._init()

        cached_until = self.py3.time_in(0)
        if self._running:
            self._time_left = ceil(self._end_time - time.perf_counter())
            time_left = ceil(self._time_left)
        else:
            time_left = ceil(self._time_left)

        vals = {"ss": int(time_left), "mm": ceil(time_left / 60)}

        if self.py3.format_contains(self.format, "mmss"):
            hours, rest = divmod(time_left, 3600)
            mins, seconds = divmod(rest, 60)

            if hours:
                vals["mmss"] = (
                    f"{hours}{self.format_separator}"
                    f"{mins:02d}{self.format_separator}{seconds:02d}"
                )
            else:
                vals["mmss"] = f"{mins}{self.format_separator}{seconds:02d}"

        if self.py3.format_contains(self.format, "bar"):
            vals["bar"] = self._setup_bar()

        formatted = self.format.format(**vals)

        if self._running:
            if self._active:
                format = self.format_active
            else:
                format = self.format_break
        else:
            if self._active:
                format = self.format_stopped
            else:
                format = self.format_break_stopped
            cached_until = self.py3.CACHE_FOREVER

        response = {
            "full_text": format.format(
                breakno=self._break_number, format=formatted, **vals
            ),
            "cached_until": cached_until,
        }

        if self._alert:
            response["urgent"] = True
            self._alert = False

        if not self._running:
            response["color"] = self.py3.COLOR_BAD
        else:
            if self._active:
                response["color"] = self.py3.COLOR_GOOD
            else:
                response["color"] = self.py3.COLOR_DEGRADED

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
