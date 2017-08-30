# -*- coding: utf-8 -*-

from __future__ import division
import random


class Py3status:
    """
    """
    format = "{bar}"
    thresholds = [(0, "good"), (40, "degraded"), (75, "bad")]
    cache_timeout = 1
    middle_char = '|'
    middle_color = None
    left_char = '|'
    left_color = None
    right_char = '|'
    right_color = None
    length = 10

    def post_config_hook(self):
        self.increasing = True
        self.value = 0

    def testBars(self):
        delta = random.randint(1, 10)
        if self.increasing:
            self.value += delta
            if self.value > 99:
                self.value = 100
                self.increasing = False
        else:
            self.value -= delta
            if self.value < 1:
                self.value = 0
                self.increasing = True

        composites = self.py3.progress_bar(self.value, length=self.length,
                middle_char=self.middle_char, middle_color=self.middle_color,
                left_char=self.left_char, left_color=self.left_color,
                right_char=self.right_char, right_color=self.right_color
                )

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'bar': composites}),
        }

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
