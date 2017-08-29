# -*- coding: utf-8 -*-

from __future__ import division
import random


class Py3status:
    """
    """
    format = "{bar}"
    thresholds = [(0, "good"), (40, "degraded"), (75, "bad")]
    cache_timeout = 1

    def post_config_hook(self):
        self.history = []

    def testBars(self):
        value = random.randint(0, 100)

        composites = self.py3.history_bar_graph(self.history, value, length=8)

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
