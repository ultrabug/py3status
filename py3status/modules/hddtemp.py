# -*- coding: utf-8 -*-
"""
Display hard drive temperatures.

hddtemp is a small utility with daemon that gives the hard drive temperature
via S.M.A.R.T. (Self-Monitoring, Analysis, and Reporting Technology). This
module requires the user-defined hddtemp daemon to be running at all times.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_hdd}')
    format_hdd: display format for hard drives
        (default '{name} [\?color=temperature {temperature}°{unit}]')
    format_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use
        *(default [(19, 'skyblue'), (24, 'deepskyblue'), (25, 'lime'),
        (41, 'yellow'), (46, 'orange'), (51, 'red'), (56, 'tomato')])*

Format placeholders:
    {format_hdd} format for hard drives

format_hdd placeholders:
    {name}        name, eg ADATA SP550
    {path}        path, eg /dev/sda
    {temperature} temperature, eg 32
    {unit}        temperature unit, eg C

Temperatures:
    Less than 25°C: Too cold     (color deepskyblue)
    25°C to 40°C: Ideal          (color good)
    41°C to 50°C: Acceptable     (color degraded)
    46°C to 50°C: Almost too hot (color orange)
    More than 50°C: Too hot      (color bad)

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    hddtemp: utility to monitor hard drive temperatures

Bible of HDD failures:
    Hard disk temperatures higher than 45°C led to higher failure rates.
    Temperatures lower than 25°C led to higher failure rates as well.
    Aging hard disk drives (3 years and older) were much more prone to
    failure when their average temperatures were 40°C and higher.

    Hard disk manufacturers often state the operating temperatures of
    their hard disk drives to be between 0°C to 60°C. This can be misleading
    because what they mean is that your hard disk will function at these
    temperatures, but it doesn't tell you anything about how long they are
    going to survive at this range.
    http://www.buildcomputers.net/hdd-temperature.html

Backblaze:
    Overall, there is not a correlation between operating temperature and
    failure rates The one exception is the Seagate Barracuda 1.5TB drives,
    which fail slightly more when they run warmer. As long as you run drives
    well within their allowed range of operating temperatures, keeping them
    cooler doesn’t matter.
    https://www.backblaze.com/blog/hard-drive-temperature-does-it-matter/

Examples:
```
# compact the format
hddtemp {
    format = 'HDD {format_hdd}'
    format_hdd = '\?color=temperature {temperature}°C'
}

# show paths instead of names
hddtemp {
    format_hdd = '{path} [\?color=temperature {temperature}°{unit}]'
}

# show more colors
hddtemp {
    gradients = True
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': u'ADATA SP550 '},
    {'full_text': u'25°C ', 'color': '#00FF00'},
    {'full_text': u'SanDisk SDSSDA240 '},
    {'full_text': u'41°C', 'color': '#FFFF00'},
]

path
[
    {'full_text': '/dev/sda '}, {'color': '#00BFFF', u'full_text': '24°C '},
    {'full_text': '/dev/sdb '}, {'color': '#00FF00', u'full_text': '25°C '},
    {'full_text': '/dev/sdc '}, {'color': '#FF0000', u'full_text': '51°C'},
]

compact
[
    {'full_text': 'HDD '},
    {'color': '#87CEEB', u'full_text': '19°C '},
    {'color': '#00BFFF', u'full_text': '24°C '},
    {'color': '#00FF00', u'full_text': '25°C '},
    {'color': '#FFFF00', u'full_text': '41°C '},
    {'color': '#FFA500', u'full_text': '46°C '},
    {'color': '#FF0000', u'full_text': '51°C '},
    {'color': '#FF6347', u'full_text': '56°C'},
]
"""

from telnetlib import Telnet
from string import printable


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{format_hdd}"
    format_hdd = u"{name} [\?color=temperature {temperature}°{unit}]"
    format_separator = " "
    thresholds = [
        (19, "skyblue"),
        (24, "deepskyblue"),
        (25, "lime"),
        (41, "yellow"),
        (46, "orange"),
        (51, "red"),
        (56, "tomato"),
    ]

    def post_config_hook(self):
        self.keys = ["path", "name", "temperature", "unit"]
        self.cache_names = {}
        self.thresholds_init = self.py3.get_color_names_list(self.format_hdd)

    def hddtemp(self):
        line = Telnet("localhost", 7634).read_all().decode("utf-8", "ignore")
        new_data = []

        for chunk in line[1:-1].split("||"):
            hdd = dict(zip(self.keys, chunk.split("|")))
            # workaround for hddtemp byte bug
            try:
                hdd["name"] = self.cache_names[hdd["name"]]
            except KeyError:
                key = "".join([x for x in hdd["name"] if x in printable]).strip()
                if key.endswith("G B") and key[-4].isdigit():
                    key = "GB".join(key.rsplit("G B", 1))
                hdd["name"] = self.cache_names[hdd["name"]] = key

            for x in self.thresholds_init:
                if x in hdd:
                    self.py3.threshold_get_color(hdd[x], x)

            new_data.append(self.py3.safe_format(self.format_hdd, hdd))

        format_separator = self.py3.safe_format(self.format_separator)
        format_hdd = self.py3.composite_join(format_separator, new_data)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"format_hdd": format_hdd}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
