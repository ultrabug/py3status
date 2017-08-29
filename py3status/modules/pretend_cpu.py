# -*- coding: utf-8 -*-

from __future__ import division
import random


class Py3status:
    """
    """
    format = "{bar}"
    thresholds = [(0, "good"), (40, "degraded"), (75, "bad")]
    cache_timeout = 1

    def testBars(self):
        values = [0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5]
        random.shuffle(values)

        composites = self.py3.concurrent_bar_graphs(values)

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
