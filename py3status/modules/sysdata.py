# -*- coding: utf-8 -*-
"""
Sysdata is a module used to display system information (RAM usage)
in i3bar (Linux systems).

NOTE: If you want py3status to show you your CPU temperature,
change value of CPUTEMP into True in Py3status class - CPUInfo function
and REMEMBER that you must install lm_sensors if you want CPU temp!

Copyright (C) <2013> <Shahin Azad [ishahinism at Gmail]>
"""

import subprocess
from time import time


class GetData:
    """Get system status
    """
    def execCMD(self, cmd, arg):
        """Take a system command and its argument, then return the result.

        Arguments:
        - `cmd`: system command.
        - `arg`: argument.
        """
        result = subprocess.check_output([cmd, arg])
        return result

    def cpu(self):
        """Get the cpu usage data from /proc/stat :
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

        #return the cpu total&idle time
        return total_cpu_time, cpu_idle_time

    def memory(self):
        """Execute 'free -m' command, grab the memory capacity and used size
        then return; Memory size 'total_mem', Used_mem, and percentage
        of used memory.

        """
        # Run 'free -m' command and make a list from output.
        mem_data = self.execCMD('free', '-m').split()
        total_mem = int(mem_data[7]) / 1024.
        used_mem = int(mem_data[15]) / 1024.
        # Caculate percentage
        used_mem_percent = int(used_mem / (total_mem / 100))

        # Results are in kilobyte.
        return total_mem, used_mem, used_mem_percent


class Py3status:

    # available configuration parameters
    cache_timeout = 10
    med_threshold = 40
    high_threshold = 75

    def __init__(self):
        self.data = GetData()
        self.cpu_total = 0
        self.cpu_idle = 0

    def cpuInfo(self, i3s_output_list, i3s_config):
        """Calculate the CPU status and return it.
        """
        response = {'full_text': ''}
        cpu_total, cpu_idle = self.data.cpu()
        used_cpu_percent = 1 - (
            float(cpu_idle-self.cpu_idle)/float(cpu_total-self.cpu_total)
            )
        self.cpu_total = cpu_total
        self.cpu_idle = cpu_idle

        if used_cpu_percent <= self.med_threshold/100.0:
            response['color'] = i3s_config['color_good']
        elif used_cpu_percent <= self.high_threshold/100.0:
            response['color'] = i3s_config['color_degraded']
        else:
            response['color'] = i3s_config['color_bad']
        #cpu temp
        CPUTEMP = False
        if CPUTEMP:
            cputemp = subprocess.check_output(
                'sensors | grep "CPU Temp" | cut -f2 -d"+" | cut -f1 -d" "',
                shell=True
            )
            cputemp = cputemp[:-1].decode('utf-8')
            response['full_text'] = "CPU: %.2f%% %s" % (
                used_cpu_percent*100,
                cputemp
            )
        else:
            response['full_text'] = "CPU: %.2f%%" % (used_cpu_percent*100)
        response['cached_until'] = time() + self.cache_timeout

        return response

    def ramInfo(self, i3s_output_list, i3s_config):
        """Calculate the memory (RAM) status and return it.
        """
        response = {'full_text': ''}
        total_mem, used_mem, used_mem_percent = self.data.memory()

        if used_mem_percent <= self.med_threshold:
            response['color'] = i3s_config['color_good']
        elif used_mem_percent <= self.high_threshold:
            response['color'] = i3s_config['color_degraded']
        else:
            response['color'] = i3s_config['color_bad']

        response['full_text'] = "RAM: %.2f/%.2f GB (%d%%)" % (
            used_mem,
            total_mem,
            used_mem_percent
        )
        response['cached_until'] = time() + self.cache_timeout

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.cpuInfo([], {}))
        print(x.ramInfo([], {}))
        sleep(1)
