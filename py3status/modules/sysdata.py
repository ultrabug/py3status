# -*- coding: utf-8 -*-
"""
Display system RAM, SWAP and CPU utilization.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    format: output format string
        *(default '[\?color=cpu CPU: {cpu_usage}%], '
        '[\?color=mem Mem: {mem_used}/{mem_total} GB ({mem_used_percent}%)]')*
    mem_unit: the unit of memory to use in report, case insensitive.
        ['dynamic', 'KiB', 'MiB', 'GiB'] (default 'GiB')
    swap_unit: the unit of swap to use in report, case insensitive.
        ['dynamic', 'KiB', 'MiB', 'GiB'] (default 'GiB')
    temp_unit: unit used for measuring the temperature ('C', 'F' or 'K')
        (default '°C')
    thresholds: thresholds to use for color changes
        (default [(0, "good"), (40, "degraded"), (75, "bad")])
    zone: thermal zone to use. If None try to guess CPU temperature
        (default None)

Format placeholders:
    {cpu_temp} cpu temperature
    {cpu_usage} cpu usage percentage
    {mem_total} total memory
    {mem_unit} unit for memory
    {mem_used} used memory
    {mem_used_percent} used memory percentage
    {swap_total} total swap
    {swap_unit} unit for swap
    {swap_used} used swap
    {swap_used_percent} used swap percentage
    {temp_unit} temperature unit

Color thresholds:
    cpu: change color based on the value of cpu_usage
    max_cpu_mem: change the color based on the max value of cpu_usage and mem_used_percent
    mem: change color based on the value of mem_used_percent
    swap: change color based on the value of swap_used_percent
    temp: change color based on the value of cpu_temp

NOTE: If using the `{cpu_temp}` option, the `sensors` command should
be available, provided by the `lm-sensors` or `lm_sensors` package.

@author Shahin Azad <ishahinism at Gmail>, shrimpza, guiniol

SAMPLE OUTPUT
[
    {'color': '#00FF00', 'full_text': 'CPU: 9.60%'},
    {'full_text': ', '},
    {'color': '#FFFF00', 'full_text': 'Mem: 1.91/3.76 GB (50.96%)'}
]
"""

from __future__ import division

import re

ONE_KIB = pow(1024, 1)  # 1 KiB in B
ONE_MIB = pow(1024, 2)  # 1 MiB in B
ONE_GIB = pow(1024, 3)  # 1 GiB in B


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

    def calc_mem_info(self, unit='GiB', memi=dict, keys=list):
        """
        Parse /proc/meminfo, grab the memory capacity and used size
        then return; Memory size 'total_mem', Used_mem, percentage
        of used memory, and units of mem (KiB, MiB, GiB).
        """

        total_mem_kib = memi[keys[0]]
        mem_free = sum([memi[item] for item in keys[1:]])

        try:
            used_mem_kib = (total_mem_kib - mem_free)
            used_mem_p = 100 * used_mem_kib / total_mem_kib
            multiplier = {
                'KiB': ONE_KIB / ONE_KIB,
                'MiB': ONE_KIB / ONE_MIB,
                'GiB': ONE_KIB / ONE_GIB,
            }
            if unit.lower() == 'dynamic':
                # If less than 1 GiB, use MiB
                if (multiplier['GiB'] * total_mem_kib) < 1:
                    unit = 'MiB'
                else:
                    unit = 'GiB'
            if unit in multiplier.keys():
                total_mem = multiplier[unit] * total_mem_kib
                used_mem = multiplier[unit] * used_mem_kib
            else:
                raise ValueError(
                    'unit [{0}] must be one of: KiB, MiB, GiB, dynamic.'.format(unit))
        except:
            total_mem, used_mem, used_mem_p = [float('nan') for i in range(3)]
            unit = 'UNKNOWN'

        # If total memory is <1GB, results are in megabytes.
        # Otherwise, results are in gigabytes.
        return total_mem, used_mem, used_mem_p, unit

    def mem(self, mem_unit='GiB', swap_unit='GiB', mem=True, swap=True):
        memi = {}
        result = {}

        with open('/proc/meminfo', 'r') as fd:
            for s in fd:
                tok = s.split()
                memi[tok[0]] = float(tok[1])

        if mem:
            result["mem"] = self.calc_mem_info(
                mem_unit,
                memi,
                ["MemTotal:", "MemFree:", "Buffers:", "Cached:"]
            )
        if swap:
            result["swap"] = self.calc_mem_info(
                swap_unit,
                memi,
                ["SwapTotal:", "SwapFree:"]
            )

        return result

    def cpuTemp(self, zone, unit):
        """
        Tries to determine CPU temperature using the 'sensors' command.
        Searches for the CPU temperature by looking for a value prefixed
        by either "CPU Temp" or "Core 0" - does not look for or average
        out temperatures of all codes if more than one.
        """

        sensors = None
        command = ['sensors']
        if unit == u'°F':
            command.append('-f')
        elif unit not in [u'°C', 'K']:
            return 'unknown unit'
        if zone:
            try:
                sensors = self.py3.command_output(command + [zone])
            except:
                pass
        if not sensors:
            sensors = self.py3.command_output(command)
        m = re.search("(Core 0|CPU Temp).+\+(.+).+\(.+", sensors)
        if m:
            cpu_temp = float(m.groups()[1].strip()[:-2])
            if unit == 'K':
                cpu_temp += 273.15
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
    mem_unit = 'GiB'
    swap_unit = 'GiB'
    temp_unit = u'°C'
    thresholds = [(0, "good"), (40, "degraded"), (75, "bad")]
    zone = None

    class Meta:

        def deprecate_function(config):
            # support old thresholds
            return {
                'thresholds': [
                    (0, 'good'),
                    (config.get('med_threshold', 40), 'degraded'),
                    (config.get('high_threshold', 75), 'bad'),
                ],
            }

        def update_deprecated_placeholder_format(config):
            padding = config.get('padding', 0)
            precision = config.get('precision', 2)
            format_vals = ':{padding}.{precision}f'.format(padding=padding,
                                                           precision=precision)
            return {
                'cpu_usage': format_vals,
                'cpu_temp': format_vals,
                'mem_total': format_vals,
                'mem_used': format_vals,
                'mem_used_percent': format_vals,
                'swap_total': format_vals,
                'swap_used': format_vals,
                'swap_used_percent': format_vals,
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
                {
                    'param': 'padding',
                    'msg': 'obsolete, use the format_* parameters',
                },
                {
                    'param': 'precision',
                    'msg': 'obsolete, use the format_* parameters',
                },
            ],
            'update_placeholder_format': [
                {
                    'function': update_deprecated_placeholder_format,
                    'format_strings': ['format']
                },
            ],
        }

        update_config = {
            'update_placeholder_format': [
                {
                    'placeholder_formats': {
                        'cpu_usage': ':.2f',
                        'cpu_temp': ':.2f',
                        'mem_total': ':.2f',
                        'mem_used': ':.2f',
                        'mem_used_percent': ':.2f',
                        'swap_total': ':.2f',
                        'swap_used': ':.2f',
                        'swap_used_percent': ':.2f',
                    },
                    'format_strings': ['format']
                },
            ],
        }

    def post_config_hook(self):
        self.data = GetData(self)
        self.cpu_total = 0
        self.cpu_idle = 0
        temp_unit = self.temp_unit.upper()
        if temp_unit in ['C', u'°C']:
            temp_unit = u'°C'
        elif temp_unit in ['F', u'°F']:
            temp_unit = u'°F'
        elif not temp_unit == 'K':
            temp_unit = 'unknown unit'
        self.values = {'temp_unit': temp_unit}
        self.temp_unit = temp_unit
        self.mem_info = self.py3.format_contains(self.format, 'mem_*')
        self.swap_info = self.py3.format_contains(self.format, 'swap_*')

    def sysData(self):
        # get CPU usage info
        if self.py3.format_contains(self.format, 'cpu_usage'):
            cpu_total, cpu_idle = self.data.cpu()
            cpu_usage = 0
            if cpu_total != self.cpu_total:
                cpu_usage = (1 - (
                    float(cpu_idle - self.cpu_idle) / float(cpu_total - self.cpu_total)
                )) * 100
            self.values['cpu_usage'] = cpu_usage
            self.cpu_total = cpu_total
            self.cpu_idle = cpu_idle
            self.py3.threshold_get_color(cpu_usage, 'cpu')

        # if specified as a formatting option, also get the CPU temperature
        if self.py3.format_contains(self.format, 'cpu_temp'):
            cpu_temp = self.data.cpuTemp(self.zone, self.temp_unit)
            self.values['cpu_temp'] = cpu_temp
            self.py3.threshold_get_color(cpu_temp, 'temp')

        # get RAM/SWAP usage info
        memi = self.data.mem(self.mem_unit, self.swap_unit, self.mem_info, self.swap_info)

        # set RAM usage info
        if self.mem_info:
            mem_total, mem_used, mem_used_percent, mem_unit = memi["mem"]
            self.values['mem_total'] = mem_total
            self.values['mem_used'] = mem_used
            self.values['mem_used_percent'] = mem_used_percent
            self.values['mem_unit'] = mem_unit
            self.py3.threshold_get_color(mem_used_percent, 'mem')

        # set SWAP usage info
        if self.swap_info:
            swap_total, swap_used, swap_used_percent, swap_unit = memi["swap"]
            self.values['swap_total'] = swap_total
            self.values['swap_used'] = swap_used
            self.values['swap_used_percent'] = swap_used_percent
            self.values['swap_unit'] = swap_unit
            self.py3.threshold_get_color(swap_used_percent, 'swap')

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
