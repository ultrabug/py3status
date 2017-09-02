# -*- coding: utf-8 -*-

from __future__ import division

# FIXME split colors config
# FIXME use gradients?

class Py3status:

    format = u'{cpu0:3d}% {cpu1:3d}% {cpu:3d}% {graph}'# {graph0} {graph1}'
    size = 10
    thresholds = [(0, 'good'), (40, 'degraded'), (75, 'bad')]
    multi_color = False

    def post_config_hook(self):

        self.cpu_list = ['cpu', 'cpu0', 'cpu1']
        self.graph_list = ['', '0', '1']

        self.values = {}
        self.cpu_data = {}
        self.graphs = {}

        for cpu in self.cpu_list:
            self.cpu_data[cpu] = (None, None)

        for graph in self.graph_list:
            self.graphs[graph] = self.py3.graph(
                'graph', size=self.size, multi_color=self.multi_color
            )

    def _get_cpu_usage(self):

        with open('/proc/stat', 'r') as f:
            while True:
                info = f.readline().split()
                cpu = info[0]
                if not cpu.startswith('cpu'):
                    break
                if cpu not in self.cpu_list:
                    continue
                total = sum(map(int, info[1:]))
                used = total - int(info[4])
                last_used, last_total = self.cpu_data[cpu]
                if last_total and total - last_total:
                    value = 100 * ((used - last_used) / (total - last_total))
                else:
                    value = 0

                self.cpu_data[cpu] = (used, total)
                self.values[cpu] = value

    def cpu(self):

        self._get_cpu_usage()
        data = self.values

        for name, graph in self.graphs.items():
            data['graph%s' % name] = graph(self.values['cpu%s' % name])

        return {
            'full_text': self.py3.safe_format(self.format, data),
            'color': self.py3.threshold_get_color(self.values['cpu']),
            'cached_until': self.py3.time_in(sync_to=1)
        }


if __name__ == "__main__":
    """

    """
    from py3status.module_test import module_test
    module_test(Py3status)
