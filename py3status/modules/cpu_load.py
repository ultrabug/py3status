# -*- coding: utf-8 -*-

from __future__ import division


class Py3status:

    format = '{bar}'
    thresholds = [(0, 'good'), (40, 'degraded'), (75, 'bad')]
    multi_color = True
    segmented = True
    size = 10

    def post_config_hook(self):

        self.last_used = None
        self.last_total = None

        if self.py3.format_contains(self.format, 'bar'):
            if self.segmented == 1:
                graph_type = 'sbar'
            else:
                graph_type = 'bar'
            self.graph = self.py3.graph(graph_type,
                                        size=self.size,
                                        multi_color=self.multi_color)
        else:
            self.graph = None

    def _get_cpu_usage(self):

        with open('/proc/stat', 'r') as f:
            info = f.readline().split()

        total = sum(map(int, info[1:]))
        used = total - int(info[4])

        if self.last_total and total - self.last_total:
            cpu = 100 * ((used - self.last_used) / (total - self.last_total))
        else:
            cpu = 0

        self.last_total = total
        self.last_used = used

        return cpu

    def cpu(self):

        value = self._get_cpu_usage()
        data = {'cpu': value}

        if self.graph:
            data['bar'] = self.graph(value)

        return {
            'full_text': self.py3.safe_format(self.format, data),
            'color': self.py3.threshold_get_color(value),
            'cached_until': self.py3.time_in(sync_to=1)
        }


if __name__ == "__main__":
    """

    """
    from py3status.module_test import module_test
    module_test(Py3status)
