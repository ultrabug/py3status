r"""
Display system RAM, SWAP and CPU utilization.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    cpu_freq_unit: the unit of CPU frequency to use in report, case insensitive.
        ['kHz', 'MHz', 'GHz'] (default 'GHz')
    cpus: specify a list of CPUs to use (default ['cpu?*'])
    format: output format string
        *(default '[\?color=cpu_used_percent CPU: {cpu_used_percent}%], '
        '[\?color=mem_used_percent Mem: {mem_used}/{mem_total} '
        '{mem_total_unit} ({mem_used_percent}%)]')*
    format_cpu: display format for CPUs
        (default '\?color=used_percent {used_percent}%')
    format_cpu_separator: show separator if more than one (default ' ')
    mem_unit: the unit of memory to use in report, case insensitive.
        ['dynamic', 'KiB', 'MiB', 'GiB'] (default 'GiB')
    swap_unit: the unit of swap to use in report, case insensitive.
        ['dynamic', 'KiB', 'MiB', 'GiB'] (default 'GiB')
    temp_unit: unit used for measuring the temperature ('C', 'F' or 'K')
        (default '°C')
    thresholds: specify color thresholds to use
        (default [(0, "good"), (40, "degraded"), (75, "bad")])
    zone: Either a path in sysfs to CPU temperature sensor, or an lm_sensors thermal zone to use.
        If None try to guess CPU temperature
        (default None)

Format placeholders:
    {cpu_freq_avg} average CPU frequency across all cores
    {cpu_freq_max} highest CPU clock frequency
    {cpu_freq_unit} unit for frequency
    {cpu_temp} cpu temperature
    {cpu_used_percent} cpu used percentage
    {format_cpu} format for CPUs
    {load1} load average over the last minute
    {load5} load average over the five minutes
    {load15} load average over the fifteen minutes
    {mem_total} total memory
    {mem_total_unit} memory total unit, eg GiB
    {mem_used} used memory
    {mem_used_unit} memory used unit, eg GiB
    {mem_used_percent} used memory percentage
    {mem_free} free memory
    {mem_free_unit} free memory unit, eg GiB
    {mem_free_percent} free memory percentage
    {swap_total} total swap
    {swap_total_unit} swap total memory unit, eg GiB
    {swap_used} used swap
    {swap_used_unit} swap used memory unit, eg GiB
    {swap_used_percent} used swap percentage
    {swap_free} free swap
    {swap_free_unit} free swap unit, eg GiB
    {swap_free_percent} free swap percentage
    {temp_unit} temperature unit

format_cpu placeholders:
    {name} cpu name, eg cpu, cpu0, cpu1, cpu2, cpu3
    {used_percent} cpu used percentage, eg 88.99

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Examples:
```
# specify a list of cpus to use. see "grep cpu /proc/stat"
sysdata {
    cpus = []                # avg + all CPUs
    cpus = ['cpu']           # avg             # same as {cpu_used_percent}
    cpus = ['cpu0', 'cpu2']  # selective CPUs  # full
    cpus = ['cpu?*']         # all CPUs        # fnmatch (default)
}

# display per cpu percents
sysdata {
    format = "{format_cpu}"
    format_cpu = "{name} [\?color=used_percent {used_percent}%]"
}

# customize per cpu padding, precision, etc
sysdata {
    format = "CPU {format_cpu}"
    format_cpu = "[\?min_length=4 [\?color=used_percent {used_percent:.0f}%]]"
}

# display per cpu histogram
sysdata {
    format = "CPU Histogram [\?color=cpu_used_percent {format_cpu}]"
    format_cpu = "[\?if=used_percent>80 ⡇|[\?if=used_percent>60 ⡆"
    format_cpu += "|[\?if=used_percent>40 ⡄|[\?if=used_percent>20 ⡀"
    format_cpu += "|⠀]]]]"
    format_cpu_separator = ""
    thresholds = [(0, "good"), (60, "degraded"), (80, "bad")]
    cache_timeout = 1
}
```

@author Shahin Azad <ishahinism at Gmail>, shrimpza, guiniol, JackDoan <me at jackdoan dot com>, farnoy

SAMPLE OUTPUT
[
    {'color': '#00FF00', 'full_text': 'CPU: 9.60%'},
    {'full_text': ', '},
    {'color': '#FFFF00', 'full_text': 'Mem: 1.91/3.76 GiB (50.96%)'}
]
"""

from fnmatch import fnmatch
from os import getloadavg
from pathlib import Path

import re


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    cpu_freq_unit = "GHz"
    cpus = ["cpu?*"]
    format = (
        r"[\?color=cpu_used_percent CPU: {cpu_used_percent}%], "
        r"[\?color=mem_used_percent Mem: {mem_used}/{mem_total} "
        "{mem_total_unit} ({mem_used_percent}%)]"
    )
    format_cpu = r"\?color=used_percent {used_percent}%"
    format_cpu_separator = " "
    mem_unit = "GiB"
    swap_unit = "GiB"
    temp_unit = "°C"
    thresholds = [(0, "good"), (40, "degraded"), (75, "bad")]
    zone = None

    class Meta:
        def update_deprecated_placeholder_format(config):
            padding = config.get("padding", 0)
            precision = config.get("precision", 2)
            format_vals = ":{padding}.{precision}f".format(
                padding=padding, precision=precision
            )
            return {
                "cpu_freq_avg": format_vals,
                "cpu_freq_max": format_vals,
                "cpu_usage": format_vals,
                "cpu_used_percent": format_vals,
                "cpu_temp": format_vals,
                "load1": format_vals,
                "load5": format_vals,
                "load15": format_vals,
                "mem_total": format_vals,
                "mem_used": format_vals,
                "mem_used_percent": format_vals,
                "mem_free": format_vals,
                "mem_free_percent": format_vals,
                "swap_total": format_vals,
                "swap_used": format_vals,
                "swap_used_percent": format_vals,
                "swap_free": format_vals,
                "swap_free_percent": format_vals,
            }

        deprecated = {
            "rename_placeholder": [
                {
                    "placeholder": "cpu_usage",
                    "new": "cpu_used_percent",
                    "format_strings": ["format"],
                },
                {
                    "placeholder": "mem_unit",
                    "new": "mem_total_unit",
                    "format_strings": ["format"],
                },
                {
                    "placeholder": "swap_unit",
                    "new": "swap_total_unit",
                    "format_strings": ["format"],
                },
            ],
            "remove": [
                {"param": "padding", "msg": "obsolete, use the format_* parameters"},
                {"param": "precision", "msg": "obsolete, use the format_* parameters"},
            ],
            "update_placeholder_format": [
                {
                    "function": update_deprecated_placeholder_format,
                    "format_strings": ["format"],
                }
            ],
        }

        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {
                        "cpu_freq_avg": ":.2f",
                        "cpu_freq_max": ":.2f",
                        "cpu_usage": ":.2f",
                        "cpu_used_percent": ":.2f",
                        "cpu_temp": ":.2f",
                        "load1": ":.2f",
                        "load5": ":.2f",
                        "load15": ":.2f",
                        "mem_total": ":.2f",
                        "mem_used": ":.2f",
                        "mem_used_percent": ":.2f",
                        "mem_free": ":.2f",
                        "mem_free_percent": ":.2f",
                        "swap_total": ":.2f",
                        "swap_used": ":.2f",
                        "swap_used_percent": ":.2f",
                        "swap_free": ":.2f",
                        "swap_free_percent": ":.2f",
                    },
                    "format_strings": ["format"],
                },
                {
                    "placeholder_formats": {"used_percent": ":.2f"},
                    "format_strings": ["format_cpu"],
                },
            ]
        }

    def post_config_hook(self):
        self.first_run = True
        temp_unit = self.temp_unit.upper()
        if temp_unit in ["C", "°C"]:
            temp_unit = "°C"
        elif temp_unit in ["F", "°F"]:
            temp_unit = "°F"
        elif not temp_unit == "K":
            temp_unit = "unknown unit"
        self.temp_unit = temp_unit
        self.init = {"meminfo": [], "stat": []}
        names_and_matches = [
            ("cpu_freq", ["cpu_freq_avg", "cpu_freq_max"]),
            ("cpu_temp", "cpu_temp"),
            ("cpu_percent", "cpu_used_percent"),
            ("cpu_per_core", "format_cpu"),
            ("load", "load*"),
            ("mem", "mem_*"),
            ("swap", "swap_*"),
        ]
        for name, match in names_and_matches:
            self.init[name] = list(
                set(
                    self.py3.get_placeholders_list(self.format, match)
                    + self.py3.get_color_names_list(self.format, match)
                )
            )
            if self.init[name]:
                if name in ["mem", "swap"]:
                    self.init["meminfo"].append(name)
                elif name in ["cpu_percent", "cpu_per_core"]:
                    self.init["stat"].append(name)

        self.thresholds_init = {
            "format": self.py3.get_color_names_list(self.format),
            "format_cpu": self.py3.get_color_names_list(self.format_cpu),
            "legacy": {
                "cpu": "cpu_used_percent",
                "temp": "cpu_temp",
                "mem": "mem_used_percent",
                "swap": "swap_used_percent",
                "load": "load1",
                "max_cpu_mem": "max_used_percent",
            },
        }

        if self.init["cpu_freq"]:
            name = sorted(self.init["cpu_freq"])[0]
            self.thresholds_init["legacy"]["cpu_freq"] = name

        if self.init["stat"]:
            self.cpus = {"cpus": self.cpus, "last": {}, "list": []}

        if self.init["cpu_temp"]:
            if self.zone is None:
                output = self.py3.command_output("sensors")

                for sensor in ["coretemp-isa-0000", "k10temp-pci-00c3"]:
                    if sensor in output:
                        self.zone = sensor
                        break

    def _get_cpuinfo(self):
        with Path("/proc/cpuinfo").open() as f:
            return [float(line.split()[-1]) for line in f if "cpu MHz" in line]

    def _calc_cpu_freqs(self, cpu_freqs, unit, keys):
        freq_avg, freq_max = None, None
        for key in keys:
            if key == "cpu_freq_avg":
                value = sum(cpu_freqs) / len(cpu_freqs) * 10 ** 6
                freq_avg, _ = self.py3.format_units(value, unit, si=True)
            elif key == "cpu_freq_max":
                value = max(cpu_freqs) * 10 ** 6
                freq_max, _ = self.py3.format_units(value, unit, si=True)
        return freq_avg, freq_max

    def _get_stat(self):
        # kernel/system statistics. man -P 'less +//proc/stat' procfs
        stat = []
        with Path("/proc/stat").open() as f:
            for line in f:
                if "cpu" in line:
                    stat.append(line)
                else:
                    return stat

    def _filter_stat(self, stat, avg=False):
        # if avg, return (name, idle, total)
        if avg:
            fields = stat[0].split()
            return "avg", int(fields[4]), sum(int(x) for x in fields[1:])

        # return a list of (name, idle, total)
        new_stat = []
        for line in stat:
            fields = line.split()
            cpu_name = fields[0]
            if self.cpus["cpus"]:
                if self.first_run:
                    for _filter in self.cpus["cpus"]:
                        if fnmatch(cpu_name, _filter):
                            self.cpus["list"].append(cpu_name)
                if cpu_name not in self.cpus["list"]:
                    continue

            new_stat.append((cpu_name, int(fields[4]), sum(int(x) for x in fields[1:])))
        return new_stat

    def _calc_mem_info(self, unit, meminfo, memory):
        """
        Parse /proc/meminfo, grab the memory capacity and used size
        then return; Memory size 'total_mem', Used_mem, percentage
        of used memory, and units of mem (KiB, MiB, GiB).
        """
        if memory:
            total_mem_kib = meminfo["MemTotal:"]
            used_mem_kib = (
                total_mem_kib
                - meminfo["MemFree:"]
                - (
                    meminfo["Buffers:"]
                    + meminfo["Cached:"]
                    + (meminfo["SReclaimable:"] - meminfo["Shmem:"])
                )
            )
            free_mem_kib = total_mem_kib - used_mem_kib
        else:
            total_mem_kib = meminfo["SwapTotal:"]
            free_mem_kib = meminfo["SwapFree:"]
            used_mem_kib = total_mem_kib - free_mem_kib

        if total_mem_kib == 0:
            used_percent = 0
            free_percent = 100
        else:
            used_percent = 100 * used_mem_kib / total_mem_kib
            free_percent = 100 - used_percent

        unit = "B" if unit == "dynamic" else unit
        (total, total_unit) = self.py3.format_units(total_mem_kib * 1024, unit)
        (used, used_unit) = self.py3.format_units(used_mem_kib * 1024, unit)
        (free, free_unit) = self.py3.format_units(free_mem_kib * 1024, unit)
        return (
            total,
            total_unit,
            used,
            used_unit,
            used_percent,
            free,
            free_unit,
            free_percent,
        )

    def _get_meminfo(self, head=28):
        with Path("/proc/meminfo").open() as f:
            info = [next(f).split() for _ in range(head)]
            return {fields[0]: float(fields[1]) for fields in info}

    def _calc_cpu_percent(self, cpu):
        name, idle, total = cpu
        last_idle = self.cpus["last"].get(name, {}).get("idle", 0)
        last_total = self.cpus["last"].get(name, {}).get("total", 0)
        used_percent = 0

        if total != last_total:
            used_percent = (1 - (idle - last_idle) / (total - last_total)) * 100

        self.cpus["last"].setdefault(name, {}).update(
            zip(["name", "idle", "total"], cpu)
        )
        return used_percent

    def _get_cputemp_with_lmsensors(self, zone=None):
        """
        Tries to determine CPU temperature using the 'sensors' command.
        Searches for the CPU temperature by looking for a value prefixed
        by either "CPU Temp" or "Core 0" - does not look for or average
        out temperatures of all codes if more than one.
        """

        sensors = None
        command = ["sensors"]
        if zone:
            try:
                sensors = self.py3.command_output(command + [zone])
            except self.py3.CommandError:
                pass
        if not sensors:
            sensors = self.py3.command_output(command)
        m = re.search(r"(Core 0|CPU Temp).+\+(.+).+\(.+", sensors)
        if m:
            cpu_temp = float(m.groups()[1].strip()[:-2])
        else:
            cpu_temp = "?"

        return cpu_temp

    def _get_cputemp(self, zone, unit):
        if zone is not None:
            try:
                with Path(zone).open() as f:
                    cpu_temp = f.readline()
                    cpu_temp = float(cpu_temp) / 1000  # convert from mdegC to degC
            except (OSError, ValueError):
                # FileNotFoundError does not exist on Python < 3.3, so we catch OSError instead
                # ValueError can be thrown if zone was a file that didn't have a float
                # if zone was not a file, it might be a sensor!
                cpu_temp = self._get_cputemp_with_lmsensors(zone=zone)

        else:
            cpu_temp = self._get_cputemp_with_lmsensors()

        if cpu_temp is float:
            if unit == "°F":
                cpu_temp = cpu_temp * 9 / 5 + 32
            elif unit == "K":
                cpu_temp += 273.15

        return cpu_temp

    def sysdata(self):
        sys = {"max_used_percent": 0, "temp_unit": self.temp_unit}

        if self.init["cpu_freq"]:
            cpu_freqs = self._calc_cpu_freqs(
                self._get_cpuinfo(), self.cpu_freq_unit, self.init["cpu_freq"]
            )
            cpu_freq_keys = ["cpu_freq_avg", "cpu_freq_max"]
            sys.update(zip(cpu_freq_keys, cpu_freqs))

        if self.init["stat"]:
            stat = self._get_stat()

            if self.init["cpu_percent"]:
                cpu = self._filter_stat(stat, avg=True)
                sys["cpu_used_percent"] = self._calc_cpu_percent(cpu)

            if self.init["cpu_per_core"]:
                cpu_keys = ["name", "used_percent"]
                new_cpu = []
                for cpu in self._filter_stat(stat):
                    cpu = dict(zip(cpu_keys, [cpu[0], self._calc_cpu_percent(cpu)]))
                    for x in self.thresholds_init["format_cpu"]:
                        if x in cpu:
                            self.py3.threshold_get_color(cpu[x], x)
                    new_cpu.append(self.py3.safe_format(self.format_cpu, cpu))

                format_cpu_separator = self.py3.safe_format(self.format_cpu_separator)
                format_cpu = self.py3.composite_join(format_cpu_separator, new_cpu)
                sys["format_cpu"] = format_cpu

        if self.init["cpu_temp"]:
            sys["cpu_temp"] = self._get_cputemp(self.zone, self.temp_unit)

        if self.init["load"]:
            load_keys = ["load1", "load5", "load15"]
            sys.update(zip(load_keys, getloadavg()))

        if self.init["meminfo"]:
            meminfo = self._get_meminfo()

            if self.init["mem"]:
                mem = self._calc_mem_info(self.mem_unit, meminfo, True)
                mem_keys = [
                    "mem_total",
                    "mem_total_unit",
                    "mem_used",
                    "mem_used_unit",
                    "mem_used_percent",
                    "mem_free",
                    "mem_free_unit",
                    "mem_free_percent",
                ]
                sys.update(zip(mem_keys, mem))

            if self.init["swap"]:
                swap = self._calc_mem_info(self.swap_unit, meminfo, False)
                swap_keys = [
                    "swap_total",
                    "swap_total_unit",
                    "swap_used",
                    "swap_used_unit",
                    "swap_used_percent",
                    "swap_free",
                    "swap_free_unit",
                    "swap_free_percent",
                ]
                sys.update(zip(swap_keys, swap))

        sys["max_used_percent"] = max(
            [perc for name, perc in sys.items() if "used_percent" in name]
        )

        for x in self.thresholds_init["format"]:
            if x in sys:
                self.py3.threshold_get_color(sys[x], x)
            elif x in self.thresholds_init["legacy"]:
                y = self.thresholds_init["legacy"][x]
                if y in sys:
                    self.py3.threshold_get_color(sys[y], x)

        self.first_run = False

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, sys),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
