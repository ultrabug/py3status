# -*- coding: utf-8 -*-
"""
Display system RAM and CPU utilization.

Configuration parameters:
    format: output format string
    high_threshold: percent to consider CPU or RAM usage as 'high load'
    med_threshold: percent to consider CPU or RAM usage as 'medium load'
    threshold_values: list of values to use for setting the color
        (default: ['cpu_usage', 'mem_used_percent'])

Format of status string placeholders:
    {cpu_temp} cpu temperature
    {cpu_usage} cpu usage percentage
    {load1} one minute load average
    {load5} five minute load average
    {load15} fifteen minute load average
    {mem_total} total memory
    {mem_used} used memory
    {mem_used_percent} used memory percentage

Color options:
    color_bad: Above high_threshold
    color_degraded: Above med_threshold
    color_good: Below or equal to med_threshold

NOTE: If using the `{cpu_temp}` option, the `sensors` command should
be available, provided by the `lm-sensors` or `lm_sensors` package.

@author Shahin Azad <ishahinism at Gmail>, shrimpza
"""

from __future__ import division

import re
import subprocess
import os


class GetData:
    """
    Get system status
    """
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

    def cpuTemp(self):
        """
        Tries to determine CPU temperature using the 'sensors' command.
        Searches for the CPU temperature by looking for a value prefixed
        by either "CPU Temp" or "Core 0" - does not look for or average
        out temperatures of all codes if more than one.
        """

        sensors = subprocess.check_output(
            'sensors',
            shell=True,
            universal_newlines=True,
        )
        m = re.search("(Core 0|CPU Temp).+\+(.+).+\(.+", sensors)
        if m:
            cpu_temp = m.groups()[1].strip()
        else:
            cpu_temp = 'Unknown'

        return cpu_temp

    def load(self):
        return os.getloadavg()

class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = "CPU: {cpu_usage:.2f}%,"\
             "Mem: {mem_used:.2f}/{mem_total:.2f} GB ({mem_used_percent:.2f}%)"
    high_threshold = 75
    med_threshold = 40
    threshold_values = ['cpu_usage', 'mem_used_percent']

    def __init__(self):
        self.data = GetData()
        self.cpu_total = 0
        self.cpu_idle = 0
        self.values = {}

    def sysData(self):
        # get CPU usage info
        if '{cpu_usage' in self.format:
            cpu_total, cpu_idle = self.data.cpu()
            self.values['cpu_usage'] = (1 - (
                float(cpu_idle-self.cpu_idle) / float(cpu_total-self.cpu_total)
                )) * 100
            self.cpu_total = cpu_total
            self.cpu_idle = cpu_idle

        # if specified as a formatting option, also get the CPU temperature
        if '{cpu_temp' in self.format:
            self.values['cpu_temp'] = self.data.cpuTemp()

        # get RAM usage info
        if ('{mem_total' in self.format or
                '{mem_used' in self.format or
                '{mem_used_percent' in self.format):
            (self.values['mem_total'],
             self.values['mem_used'],
             self.values['mem_used_percent']) = self.data.memory()

        # get load
        if '{load' in self.format:
            (self.values['load1'],
             self.values['load5'],
             self.values['load15']) = self.data.load()

        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, self.values),
        }

        threshold = 0
        for value in self.threshold_values:
            if value in self.format:
                threshold = max(threshold, self.values[value])

        if threshold <= self.med_threshold:
            response['color'] = self.py3.COLOR_GOOD
        elif (threshold <= self.high_threshold):
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
