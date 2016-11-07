# -*- coding: utf-8 -*-
"""
Display system RAM and CPU utilization.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    format: output format string
        *(default '[\?color=cpu CPU: {cpu_usage}%], '
        '[\?color=mem Mem: {mem_used}/{mem_total} GB ({mem_used_percent}%)]')*
    padding: length of space padding to use on the left
        (default 0)
    precision: precision of values
        (default 2)
    thresholds: thresholds to use for color changes
        (default [(0, "good"), (40, "degraded"), (75, "high")])
    zone: thermal zone to use. If None try to guess CPU temperature
        (default None)

Format placeholders:
    {cpu_temp} cpu temperature
    {cpu_usage} cpu usage percentage
    {mem_total} total memory
    {mem_used} used memory
    {mem_used_percent} used memory percentage

Color thresholds:
    cpu: change color based on the value of cpu_usage
    max_cpu_mem: change the color based on the max value of cpu_usage and mem_used_percent
    mem: change color based on the value of mem_used_percent
    temp: change color based on the value of cpu_temp

NOTE: If using the `{cpu_temp}` option, the `sensors` command should
be available, provided by the `lm-sensors` or `lm_sensors` package.

@author Shahin Azad <ishahinism at Gmail>, shrimpza, guiniol
"""

from __future__ import division

import re


class GetData:
    """
    Get system status
    """
    def __init__(self, parent):
        self.py3 = parent.py3

    def cpu(self):
        """
        Get the cpu usage data from /proc/stat :
          cpu  2255 34 2290 22625563 6290 127 456 0 0
          - user: normal processes executing in user mode
          - nice: niced processes executing in user mode
          - system: processes executing in kernel mode
          - idle: twiddling thumbs
          - iowait: waiting for I/O to complete
          - irq: servicing interrupts
          - softirq: servicing softirqs
          - steal: involuntary wait
          - guest: running a normal guest
          - guest_nice: running a niced guest
        These numbers identify the amount of time the CPU has spent performing
        different kinds of work.  Time units are in USER_HZ
        (typically hundredths of a second)
        """
        with open('/proc/stat', 'r') as fd:
            line = fd.readline()
        cpu_data = line.split()
        total_cpu_time = sum(map(int, cpu_data[1:]))
        cpu_idle_time = int(cpu_data[4])

        # return the cpu total&idle time
        return total_cpu_time, cpu_idle_time

    def memory(self):
        """
        Parse /proc/meminfo, grab the memory capacity and used size
        then return; Memory size 'total_mem', Used_mem, and percentage
        of used memory.
        """

        memi = {}
        with open('/proc/meminfo', 'r') as fd:
            for s in fd:
                tok = s.split()
                memi[tok[0]] = float(tok[1]) / (1 << 20)

        try:
            total_mem = memi["MemTotal:"]
            used_mem = (total_mem -
                        memi["MemFree:"] -
                        memi["Buffers:"] -
                        memi["Cached:"])
            used_mem_p = int(used_mem / (total_mem / 100))
        except:
            total_mem, used_mem, used_mem_p = [float('nan') for i in range(3)]

        # Results are in gigabytes
        return total_mem, used_mem, used_mem_p

    def cpuTemp(self, zone):
        """
        Tries to determine CPU temperature using the 'sensors' command.
        Searches for the CPU temperature by looking for a value prefixed
        by either "CPU Temp" or "Core 0" - does not look for or average
        out temperatures of all codes if more than one.
        """

        sensors = None
        if zone:
            try:
                sensors = self.py3.command_output(['sensors', zone])
            except:
                sensors = None
        if not sensors:
            sensors = self.py3.command_output('sensors')
        m = re.search("(Core 0|CPU Temp).+\+(.+).+\(.+", sensors)
        if m:
            cpu_temp = float(m.groups()[1].strip()[:-2])
        else:
            cpu_temp = '?'

        return cpu_temp


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = "[\?color=cpu CPU: {cpu_usage}%], " \
        "[\?color=mem Mem: {mem_used}/{mem_total} GB ({mem_used_percent}%)]"
    padding = 0
    precision = 2
    thresholds = [(0, "good"), (40, "degraded"), (75, "high")]
    zone = None

    class Meta:

        def deprecate_function(config):
            # support old thresholds
            return {
                    'thresholds': [
                        (0, 'good'),
                        (config.get('med_threshold', 40), 'degraded'),
                        (config.get('high_threshold', 75), 'bad'),
                        ]
                    }

        deprecated = {
                'function': [
                    {'function': deprecate_function},
                    ],
                'remove': [
                    {
                        'param': 'high_threshold',
                        'msg': 'obsolete, set using thresholds parameter',
                        },
                    {
                        'param': 'med_threshold',
                        'msg': 'obsolete, set using thresholds parameter',
                        },
                    ]
                }

    def post_config_hook(self):
        self.data = GetData(self)
        self.cpu_total = 0
        self.cpu_idle = 0
        self.values = {}

    def sysData(self):
        value_format = '{{:{}.{}f}}'.format(self.padding, self.precision)

        # get CPU usage info
        if '{cpu_usage}' in self.format:
            cpu_total, cpu_idle = self.data.cpu()
            cpu_usage = (1 - (
                float(cpu_idle-self.cpu_idle) / float(cpu_total-self.cpu_total)
                )) * 100
            self.values['cpu_usage'] = value_format.format(cpu_usage)
            self.cpu_total = cpu_total
            self.cpu_idle = cpu_idle
            self.py3.threshold_get_color(cpu_usage, 'cpu')

        # if specified as a formatting option, also get the CPU temperature
        if '{cpu_temp}' in self.format:
            cpu_temp = self.data.cpuTemp(self.zone)
            try:
                self.values['cpu_temp'] = (value_format + '°C').format(cpu_temp)
            except ValueError:
                self.values['cpu_temp'] = u'{}°C'.format(cpu_temp)
            self.py3.threshold_get_color(cpu_temp, 'temp')

        # get RAM usage info
        if '{mem_' in self.format:
            mem_total, mem_used, mem_used_percent = self.data.memory()
            self.values['mem_total'] = value_format.format(mem_total)
            self.values['mem_used'] = value_format.format(mem_used)
            self.values['mem_used_percent'] = value_format.format(mem_used_percent)
            self.py3.threshold_get_color(mem_used_percent, 'mem')

        try:
            self.py3.threshold_get_color(max(cpu_usage, mem_used_percent), 'max_cpu_mem')
        except:
            try:
                self.py3.threshold_get_color(cpu_usage, 'max_cpu_mem')
            except:
                try:
                    self.py3.threshold_get_color(mem_used_percent, 'max_cpu_mem')
                except:
                    pass

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, self.values)
        }

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
