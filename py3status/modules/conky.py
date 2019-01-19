# -*- coding: utf-8 -*-
"""
Display Conky objects/variables on the bar.

Configuration parameters:
    config: specify configuration settings for conky (default {})
    format: display format for this module (default None)
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    According to man page, Conky has more than 250 built-in objects/variables.

    See `man -P 'less -p OBJECTS/VARIABLES' conky` for a full list of Conky
    objects/variables to use. Not all of Conky objects/variables will be
    supported or usable.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder
         Replace spaces with periods.

Examples:
```
# add conky config options
# See `man -P "less -p 'CONFIGURATION SETTINGS'" conky` for a full list
# of Conky configuration options. Not all of Conky configuration options
# will be supported or usable.
conky {
    config = {
        'update_interval': 10             # update interval for conky
        'update_interval_on_battery': 60  # update interval when on battery
        'format_human_readable': True,    # if False, print in bytes
        'short_units': True,              # shortens units, eg kiB->k, GiB->G
        'uppercase': True,                # upper placeholders
    }
}

# display ip address
order += "conky addr"
conky addr {
    format = 'IP [\?color=orange {addr eno1}]'
}

# display load averages
order += "conky loadavg"
conky loadavg {
    format = 'Loadavg '
    format += '[\?color=lightgreen {loadavg 1} ]'
    format += '[\?color=lightgreen {loadavg 2} ]'
    format += '[\?color=lightgreen {loadavg 3}]'
}

# exec commands at different intervals, eg 5s, 60s, and 3600s
order += "conky date"
conky date {
    format = 'Exec '
    format += '[\?color=good {execi 5 "date"}] '
    format += '[\?color=degraded {execi 60 "uptime -p"}] '
    format += '[\?color=bad {execi 3600 "uptime -s"}]'
}

# display diskio read, write, etc
order += "conky diskio"
conky diskio {
    format = 'Disk IO [\?color=darkgray&show sda] '
    format += '[\?color=lightskyblue '
    format += '{diskio_read sda}/{diskio_write sda} '
    format += '({diskio sda})]'

    # format += ' '
    # format += '[\?color=darkgray&show sdb] '
    # format += '[\?color=lightskyblue '
    # format += '{diskio_read sdb}/{diskio_write sdb} '
    # format += '({diskio sdb})]'
    config = {'short_units': True}
}

# display total number of processes and running processes
order += "conky proc"
conky proc {
    format = 'Processes [\?color=cyan {processes}/{running_processes}]'
}

# display top 3 cpu (+mem_res) processes
order += "conky top_cpu" {
conky top_cpu {
    format = 'Top [\?color=darkgray '
    format += '{top name 1} '
    format += '[\?color=deepskyblue {top mem_res 1}] '
    format += '[\?color=lightskyblue {top cpu 1}%] '

    format += '{top name 2} '
    format += '[\?color=deepskyblue {top mem_res 2}] '
    format += '[\?color=lightskyblue {top cpu 2}%] '

    format += '{top name 3} '
    format += '[\?color=deepskyblue {top mem_res 3}] '
    format += '[\?color=lightskyblue {top cpu 3}%]]'
    config = {'short_units': True}
}

# display top 3 memory processes
order += "conky top_mem"
conky top_mem {
    format = 'Top Mem [\?color=darkgray '
    format += '{top_mem name 1} '
    format += '[\?color=yellowgreen {top_mem mem_res 1}] '
    format += '[\?color=lightgreen {top_mem mem 1}%] '

    format += '{top_mem name 2} '
    format += '[\?color=yellowgreen {top_mem mem_res 2}] '
    format += '[\?color=lightgreen {top_mem mem 2}%] '

    format += '{top_mem name 3} '
    format += '[\?color=yellowgreen {top_mem mem_res 3}] '
    format += '[\?color=lightgreen {top_mem mem 3}%]]'
    config = {'short_units': True}
}

# display memory, memperc, membar + thresholds
order += "conky memory"
conky memory {
    format = 'Memory [\?color=lightskyblue {mem}/{memmax}] '
    format += '[\?color=memperc {memperc}% \[{membar}\]]'
    thresholds = [
        (0, 'darkgray'), (0.001, 'good'), (50, 'degraded'),
        (75, 'orange'), (85, 'bad')
    ]
}

# display swap, swapperc, swapbar + thresholds
order += "conky swap"
conky swap {
    format = 'Swap [\?color=lightcoral {swap}/{swapmax}] '
    format += '[\?color=swapperc {swapperc}% \[{swapbar}\]]'
    thresholds = [
        (0, 'darkgray'), (0.001, 'good'), (50, 'degraded'),
        (75, 'orange'), (85, 'bad')
    ]
}

# display up/down speed and up/down total
order += "conky network"
conky network {
    format = 'Speed [\?color=title {upspeed eno1}/{downspeed eno1}] '
    format += 'Total [\?color=title {totalup eno1}/{totaldown eno1}]'
    color_title = '#ff6699'
}

# display file systems + thresholds
order += "conky filesystem"
conky filesystem {
    # home filesystem
    format = 'Home [\?color=violet {fs_used /home}/{fs_size /home} '
    format += '[\?color=fs_used_perc./home '
    format += '{fs_used_perc /home}% \[{fs_bar /home}\]]]'

    # hdd filesystem
    # format += ' HDD [\?color=violet {fs_used '
    # format += '/run/media/user/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    # format += '}/{fs_size '
    # format += '/run/media/user/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    # format += '}[\?color=fs_used_perc.'
    # format += '/run/media/user/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    # format += ' {fs_used_perc '
    # format += '/run/media/user/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    # format += '}% \[{fs_bar '
    # format += '/run/media/user/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    # format += '}\]]]'

    thresholds = [
        (0, 'darkgray'), (0.001, 'good'), (50, 'degraded'),
        (75, 'orange'), (85, 'bad')
    ]
}

# show cpu percents/bars + thresholds
order += "conky cpu"
conky cpu {
    format = 'CPU '
    format += '[\?color=cpu.cpu0 {cpu cpu0}% {cpubar cpu0}] '
    format += '[\?color=cpu.cpu1 {cpu cpu1}% {cpubar cpu1}] '
    format += '[\?color=cpu.cpu2 {cpu cpu2}% {cpubar cpu2}] '
    format += '[\?color=cpu.cpu3 {cpu cpu3}% {cpubar cpu3}]'

    thresholds = [
        (0, 'darkgray'), (0.001, 'good'), (50, 'degraded'),
        (75, 'orange'), (85, 'bad')
    ]
}

# show more examples, many outputs
order += "conky info"
conky info {
    format = '[\?color=title&show OS] [\?color=output {distribution}] '
    format += '[\?color=title&show CPU] [\?color=output {cpu cpu0}%] '
    format += '[\?color=title&show MEM] '
    format += '[\?color=output {mem}/{memmax} ({memperc}%)] '
    format += '[\?color=title&show HDD] [\?color=output {fs_used_perc}%] '
    format += '[\?color=title&show Kernel] [\?color=output {kernel}] '
    format += '[\?color=title&show Loadavg] [\?color=output {loadavg 1}] '
    format += '[\?color=title&show Uptime] [\?color=output {uptime}] '
    format += '[\?color=title&show Freq GHZ] [\?color=output {freq_g}]'
    color_title = '#ffffff'
    color_output = '#00bfff'
}

# change console bars - shoutout to su8 for adding this
conky {
    config = {
        'console_bar_fill': "'#'",
        'console_bar_unfill': "'_'",
        'default_bar_width': 10,
    }
}

# display nvidia stats - shoutout to brndnmtthws for fixing this
# See `man -P 'less -p nvidia\ argument' conky` for more nvidia variables.
order += "conky nvidia"
conky nvidia {
    format = 'GPU Temp [\?color=greenyellow {nvidia temp}] '
    format += 'GPU Freq [\?color=greenyellow {nvidia gpufreq}] '
    format += 'Mem Freq [\?color=greenyellow {nvidia memfreq}] '
    format += 'MTR Freq [\?color=greenyellow {nvidia mtrfreq}] '
    format += 'Perf [\?color=greenyellow {nvidia perflevel}] '
    format += 'Mem Perc [\?color=greenyellow {nvidia memperc}]'
    config = {
        'nvidia_display': "':0'"
    }
}
```

@author lasers

SAMPLE OUTPUT
[{'full_text': 'IP '}, {'full_text': u'192.168.1.113', 'color': '#ffa500'}]

diskio
[
    {'full_text': 'Disk IO '},
    {'full_text': 'sda ', 'color': '#a9a9a9'},
    {'full_text': '0B/285K (285K) ', 'color': '#87cefa'},
    {'full_text': 'sdb ', 'color': '#a9a9a9'},
    {'full_text': '40K/116K (156K)', 'color': '#87cefa'},
]

processes
[
    {'full_text': 'Processes '}, {'full_text': u'342/0', 'color': '#00ffff'}
]

top
[
    {'full_text': 'Top '},
    {'full_text': 'firefox-esr ', 'color': '#a9a9a9'},
    {'full_text': '512M ', 'color': '#00bfff'},
    {'full_text': '0.25% ', 'color': '#87cefa'},
    {'full_text': 'htop ', 'color': '#a9a9a9'},
    {'full_text': '2.93M ', 'color': '#00bfff'},
    {'full_text': '0.17%', 'color': '#87cefa'},
]

top_mem
[
    {'full_text': 'Top Mem '},
    {'full_text': 'chrome ', 'color': '#a9a9a9'},
    {'full_text': '607M ', 'color': '#006400'},
    {'full_text': '7.86% ', 'color': '#90ee90'},
    {'full_text': 'thunderbird ', 'color': '#a9a9a9'},
    {'full_text': '449M ', 'color': '#006400'},
    {'full_text': '5.82%', 'color': '#90ee90'},
]

network
[
    {'full_text': 'Speed '},
    {'color': '#ff6699', 'full_text': '15B/84B '},
    {'full_text': 'Total '},
    {'color': '#ff6699', 'full_text': '249MiB/4.27GiB'},
]

memory
[
    {'full_text': 'Memory '},
    {'full_text': '2.68G/7.72G ', 'color': '#87cefa'},
    {'full_text': '34% [###.......]', 'color': '#8ae234'}
]

swap
[
    {'full_text': 'Swap '},
    {'full_text': '4.5MiB/7.72GiB ', 'color': '#f08080'},
    {'full_text': '0% [..........]', 'color': '#a9a9a9'}
]

disk
[
    {'full_text': 'Home '},
    {'full_text': '167G/431G ', 'color': '#ee82ee'},
    {'full_text': '38% [####......]', 'color': '#8ae234'},
]

nvidia
[
    {'full_text': 'GPU Temp '}, {'full_text': '64 ', 'color': '#adff2f'},
    {'full_text': 'GPU Freq '}, {'full_text': '460 ', 'color': '#adff2f'},
    {'full_text': 'Mem Freq '}, {'full_text': '695', 'color': '#adff2f'},
]

nvidia
[
    {'full_text': 'MTR Freq '}, {'full_text': '1390 ', 'color': '#adff2f'},
    {'full_text': 'Perf '}, {'full_text': '1 ', 'color': '#adff2f'},
    {'full_text': 'Mem Perc '}, {'full_text': '61', 'color': '#adff2f'},
]

bar
[
    {'full_text': '#.... ', 'color': '#ffffff'},
    {'full_text': '##... ', 'color': '#00FF00'},
    {'full_text': '###.. ', 'color': '#FFA500'},
    {'full_text': '####. ', 'color': '#FFFF00'},
    {'full_text': '#####', 'color': '#FF0000'},
]
"""

from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from tempfile import NamedTemporaryFile
from json import dumps
from os import remove as os_remove

STRING_NOT_INSTALLED = "not installed"
STRING_MISSING_FORMAT = "missing format"


class Py3status:
    """
    """

    # available configuration parameters
    config = {}
    format = None
    thresholds = []

    def post_config_hook(self):
        if not self.py3.check_commands("conky"):
            raise Exception(STRING_NOT_INSTALLED)
        elif not self.format:
            raise Exception(STRING_MISSING_FORMAT)

        # placeholders
        placeholders = self.py3.get_placeholders_list(self.format)
        _placeholders = [x.replace(".", " ") for x in placeholders]
        colors = self.py3.get_color_names_list(self.format)
        _colors = []
        for color in colors:
            if not getattr(self, "color_{}".format(color), None):
                _colors.append(color.replace(".", " "))
        self.placeholders = placeholders + colors
        conky_placeholders = _placeholders + _colors

        # init
        self.cache_names = {}
        self.thresholds_init = colors
        self.config.update({"out_to_x": False, "out_to_console": True})
        self.separator = "|SEPARATOR|"  # must be upper

        # make an output.
        config = dumps(self.config, separators=(",", "=")).replace('"', "")
        text = self.separator.join(["${%s}" % x for x in conky_placeholders])
        tmp = "conky.config = {}\nconky.text = [[{}]]".format(config, text)

        # write tmp output to '/tmp/py3status-conky_*', make a command
        self.tmpfile = NamedTemporaryFile(
            prefix="py3status_conky-", suffix=".conf", delete=False
        )
        self.tmpfile.write(tmp if self.py3.is_python_2() else str.encode(tmp))
        self.tmpfile.close()
        self.conky_command = "conky -c {}".format(self.tmpfile.name).split()

        # thread
        self.line = ""
        self.error = None
        self.process = None
        self.t = Thread(target=self._start_loop)
        self.t.daemon = True
        self.t.start()

    def _cleanup(self):
        self.process.kill()
        os_remove(self.tmpfile.name)
        self.py3.update()

    def _start_loop(self):
        try:
            self.process = Popen(self.conky_command, stdout=PIPE, stderr=STDOUT)
            while True:
                line = self.process.stdout.readline().decode()
                if self.process.poll() is not None or "conky:" in line:
                    raise Exception(line)
                if self.line != line:
                    self.line = line
                    self.py3.update()
        except Exception as err:
            self.error = " ".join(format(err).split()[1:])
        finally:
            self._cleanup()

    def conky(self):
        if self.error:
            self.py3.error(self.error, self.py3.CACHE_FOREVER)

        conky_data = map(str.strip, self.line.split(self.separator))
        conky_data = dict(zip(self.placeholders, conky_data))

        if self.thresholds_init:
            for k in list(conky_data):
                try:
                    conky_data[self.cache_names[k]] = conky_data[k]
                except KeyError:
                    self.cache_names[k] = k.replace(" ", ".")
                    conky_data[self.cache_names[k]] = conky_data[k]

            for x in self.thresholds_init:
                if x in conky_data:
                    self.py3.threshold_get_color(conky_data[x], x)

        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, conky_data),
        }

    def kill(self):
        self._cleanup()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
