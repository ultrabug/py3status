"""
A simple countdown timer.

This is a very basic countdown timer.  You can change the timer length as well
as pausing, restarting and resetting it.  Currently this is more of a demo of a
composite.

Each part of the timer can be changed independently hours, minutes, seconds using
mouse buttons 4 and 5 (scroll wheel).
Button 1 starts/pauses the countdown.
Button 2 resets timer.

Configuration parameters:
    format: display format for this module (default 'Timer {timer}')
    sound: play sound file path when the timer ends (default None)
    time: number of seconds to start countdown with (default 60)

Format placeholders:
    {timer} display hours:minutes:seconds

@author tobes

SAMPLE OUTPUT
{'full_text': 'Timer 0:01:00'}

running
[
    {'full_text': 'Timer '},
    {'color': '#00FF00', 'full_text': '0'},
    {'full_text': ':'},
    {'color': '#00FF00', 'full_text': '00'},
    {'full_text': ':'},
    {'color': '#00FF00', 'full_text': '54'},
]

paused
[
    {'full_text': 'Timer '},
    {'color': '#FFFF00', 'full_text': '0'},
    {'full_text': ':'},
    {'color': '#FFFF00', 'full_text': '00'},
    {'full_text': ':'},
    {'color': '#FFFF00', 'full_text': '54'},
]
"""

import time
from threading import Timer


class Py3status:
    """
    """

    # available configuration parameters
    format = "Timer {timer}"
    sound = None
    time = 60

    def post_config_hook(self):
        self.running = False
        self.end_time = None
        self.time_left = None
        self.color = None
        self.alarm_timer = None
        self.alarm = False
        self.done = False

    def _time_up(self):
        """
        Called when the timer expires
        """
        self.running = False
        self.color = self.py3.COLOR_BAD
        self.time_left = 0
        self.done = True
        if self.sound:
            self.py3.play_sound(self.sound)
            self.alarm = True
        self.timer()

    def timer(self):
        if self.running or self.done:
            t = int(self.end_time - time.perf_counter())
            if t <= 0:
                t = 0
        else:
            if self.time_left:
                t = self.time_left
            else:
                t = self.time

        hours, t = divmod(t, 3600)
        minutes, t = divmod(t, 60)
        seconds = t

        if self.running:
            cached_until = self.py3.time_in(0, offset=self.cache_offset)
        else:
            cached_until = self.py3.CACHE_FOREVER

        composites = [
            {"full_text": str(hours), "color": self.color, "index": "hours"},
            {"full_text": ":"},
            {
                "full_text": format(minutes, "02d"),
                "color": self.color,
                "index": "minutes",
            },
            {"full_text": ":"},
            {
                "full_text": format(seconds, "02d"),
                "color": self.color,
                "index": "seconds",
            },
        ]

        timer = self.py3.composite_create(composites)

        response = {
            "cached_until": cached_until,
            "full_text": self.py3.safe_format(self.format, {"timer": timer}),
        }
        if self.done:
            response["urgent"] = True
        return response

    def on_click(self, event):
        deltas = {"hours": 3600, "minutes": 60, "seconds": 1}
        index = event["index"]
        button = event["button"]

        # If played an alarm sound, then cancel the sound and urgent on any
        # button press... otherwise, we only cancel an urgent
        if self.done:
            self.done = False
            if self.alarm:
                self.py3.stop_sound()
                self.alarm = False
            return

        if button == 1:
            if self.running:
                # pause timer
                self.running = False
                self.time_left = int(self.end_time - time.perf_counter())
                self.color = self.py3.COLOR_DEGRADED
                if self.alarm_timer:
                    self.alarm_timer.cancel()
            else:
                # start/restart timer
                self.running = True
                if self.time_left:
                    self.end_time = time.perf_counter() + self.time_left
                else:
                    self.end_time = time.perf_counter() + self.time
                self.cache_offset = self.end_time % 1
                self.color = self.py3.COLOR_GOOD
                if self.alarm_timer:
                    self.alarm_timer.cancel()
                self.done = False
                self.alarm_timer = Timer(self.time_left or self.time, self._time_up)
                self.alarm_timer.start()

        if button == 2:
            self.running = False
            self.time_left = None
            self.color = None
            self.done = False
            if self.alarm_timer:
                self.alarm_timer.cancel()

        if not self.running:
            self.done = False
            # change timer section HH:MM:SS
            if self.time_left:
                t = self.time_left
            else:
                t = self.time
            if button == 4:
                t += deltas.get(index, 0)
            if button == 5:
                t -= deltas.get(index, 0)
                if t < 0:
                    t = 0
            if self.time_left:
                self.time_left = t
            else:
                self.time = t

    def kill(self):
        # remove any timer
        if self.alarm_timer:
            self.alarm_timer.cancel()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
