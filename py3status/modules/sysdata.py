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
    {load1} load average over the last minute
    {load5} load average over the five minutes
    {load15} load average over the fifteen minutes
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
    load: change color based on the value of load1
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
from os import getloadavg

import re

ONE_KIB = pow(1024, 1)  # 1 KiB in B
ONE_MIB = pow(1024, 2)  # 1 MiB in B
ONE_GIB = pow(1024, 3)  # 1 GiB in B


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
                'load1': format_vals,
                'load5': format_vals,
                'load15': format_vals,
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
                        'load1': ':.2f',
                        'load5': ':.2f',
                        'load15': ':.2f',
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
        self.last_cpu = {}
        temp_unit = self.temp_unit.upper()
        if temp_unit in ['C', u'°C']:
            temp_unit = u'°C'
        elif temp_unit in ['F', u'°F']:
            temp_unit = u'°F'
        elif not temp_unit == 'K':
            temp_unit = 'unknown unit'
        self.temp_unit = temp_unit
        self.init = {'meminfo': []}
        names = ['cpu_temp', 'cpu_usage', 'load', 'mem', 'swap']
        placeholders = ['cpu_temp', 'cpu_usage', 'load*', 'mem_*', 'swap_*']
        for name, placeholder in zip(names, placeholders):
            self.init[name] = self.py3.format_contains(self.format, placeholder)
            if name in ['mem', 'swap'] and self.init[name]:
                self.init['meminfo'].append(name)

    def _get_stat(self):
        # miscellaneous kernel statistics https://git.io/vn21n
        with open('/proc/stat') as f:
            fields = f.readline().split()
            return {
                'total': sum(map(int, fields[1:])),
                'idle': int(fields[4]),
            }

    def _calc_mem_info(self, unit='GiB', memi=dict, keys=list):
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

    def _get_mem(self, mem_unit='GiB', swap_unit='GiB', mem=True, swap=True):
        memi = {}
        result = {}

        with open('/proc/meminfo', 'r') as fd:
            for s in fd:
                tok = s.split()
                memi[tok[0]] = float(tok[1])

        if mem:
            result["mem"] = self._calc_mem_info(
                mem_unit,
                memi,
                ["MemTotal:", "MemFree:", "Buffers:", "Cached:"]
            )
        if swap:
            result["swap"] = self._calc_mem_info(
                swap_unit,
                memi,
                ["SwapTotal:", "SwapFree:"]
            )

        return result

    def _calc_cpu_percent(self, cpu):
        cpu_usage = 0
        if cpu['total'] != self.last_cpu.get('total'):
            cpu_usage = (1 - (
                (cpu['idle'] - self.last_cpu.get('idle', 0)) /
                (cpu['total'] - self.last_cpu.get('total', 0))
            )) * 100

        self.last_cpu.update(cpu)
        return cpu_usage

    def _get_cputemp(self, zone, unit):
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

    def sysdata(self):
        sys = {'temp_unit': self.temp_unit}

        if self.init['cpu_usage']:
            sys['cpu_usage'] = self._calc_cpu_percent(self._get_stat())
            self.py3.threshold_get_color(sys['cpu_usage'], 'cpu')

        if self.init['cpu_temp']:
            sys['cpu_temp'] = self._get_cputemp(self.zone, self.temp_unit)
            self.py3.threshold_get_color(sys['cpu_temp'], 'temp')

        if self.init['meminfo']:
            memi = self._get_mem(
                self.mem_unit, self.swap_unit, self.init['mem'], self.init['swap'])

            if self.init['mem']:
                mem_keys = [
                    'mem_total', 'mem_used', 'mem_used_percent', 'mem_unit']
                sys.update(zip(mem_keys, memi['mem']))
                self.py3.threshold_get_color(sys['mem_used_percent'], 'mem')

            if self.init['swap']:
                swap_keys = [
                    'swap_total', 'swap_used', 'swap_used_percent', 'swap_unit']
                sys.update(zip(swap_keys, memi['swap']))
                self.py3.threshold_get_color(sys['swap_used_percent'], 'swap')

        if self.init['load']:
            load_keys = ['load1', 'load5', 'load15']
            sys.update(zip(load_keys, getloadavg()))
            self.py3.threshold_get_color(sys['load1'], 'load')

        try:
            self.py3.threshold_get_color(
                max(sys['cpu_usage'], sys['mem_used_percent']), 'max_cpu_mem')
        except:
            try:
                self.py3.threshold_get_color(sys['cpu_usage'], 'max_cpu_mem')
            except:
                try:
                    self.py3.threshold_get_color(
                        sys['mem_used_percent'], 'max_cpu_mem')
                except:
                    pass

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, sys)
        }

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
