# -*- coding: utf-8 -*-
"""
Display average system load over a period of time.

In UNIX computing, the system load is a measure of the amount of computational
work that a computer system performs. The load average represents the average
system load over a period of time. It conventionally appears in the form of
three numbers which represent the system load during the last one-, five-,
and fifteen-minute periods.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module
        *(default 'Loadavg [\?color=1avg {1min}] '
        '[\?color=5avg {5min}] [\?color=15avg {15min}]')*
    thresholds: specify color thresholds to use
        *(default [(0, '#9dd7fb'), (20, 'good'),
        (40, 'degraded'), (60, '#ffa500'), (80, 'bad')])*

Format placeholders:
    {1min} load average during the last 1-minute, eg 1.44
    {5min} load average during the last 5-minutes, eg 1.66
    {15min} load average during the last 15-minutes, eg 1.52
    {1avg} load average percentage during the last 1-minute, eg 12.00
    {5avg} load average percentage during the last 5-minutes, eg 13.83
    {15avg} load average percentage during the last 15-minutes, eg 12.67

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Notes:
    http://blog.scoutapp.com/articles/2009/07/31/understanding-load-averages
    http://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html

Examples:
```
# show load averages with static colors
loadavg {
    format = 'Loadavg [\?color=orange {1min} ][\?color=gold {5min} {15min}]'
}

# remove prefix - easy copy and paste
loadavg {
    format = '[\?color=1avg {1min}] '
    format += '[\?color=5avg {5min}] '
    format += '[\?color=15avg {15min}]'
}

# show detailed load averages + percentages
loadavg {
    format = 'Loadavg [\?color=darkgray '
    format += '1min [\?color=1avg {1min}]\|[\?color=1avg {1avg}%] '
    format += '5min [\?color=5avg {5min}]\|[\?color=5avg {5avg}%] '
    format += '15min [\?color=15avg {15min}]\|[\?color=15avg {15avg}%]]'
}

# show load averages with different colors + thresholds
loadavg {
    # htop - default
        (0, '#9dd7fb'),     # 1avg
        (0, 'cyan'),        # 5avg
        (0, 'darkcyan'),    $ 15avg

    # htop - monochrome
        (0, '#9dd7fb'),     # 1avg
        (0, None),          # 5avg
        (0, None),          # 15avg

    # htop - black night
        (0, 'greenyellow'), # 1avg
        (0, 'limegreen'),   # 5avg
        (0, 'limegreen'),   # 15avg

    # htop - mc
        (0, '#ffffff'),     # 1avg
        (0, '#aaaaaa'),     # 5avg
        (0, '#555555'),     # 15avg

    # three shades of blue
        (0, '#87cefa'),     # 1avg
        (0, '#4bb6f8'),     # 5avg
        (0, '#0991e5'),     # 15avg

    # three shades of gray
        (0, '#dddddd'),     # 1avg
        (0, '#bbbbbb'),     # 5avg
        (0, '#999999'),     # 15avg

    # htop - mc and three shades of gray is similar. htop - mc
    # have higher contrast between time periods over three shades
    # of gray for better readability. your mileage may vary.

    thresholds = {
        '1avg': [
            (0, 'REPLACE_ME'),
            (20, 'good'), (40, 'degraded'),
            (60, '#ffa500'), (80, 'bad')
        ],
        '5avg': [
            (0, 'REPLACE_ME'),
            (20, 'good'), (40, 'degraded'),
            (60, '#ffa500'), (80, 'bad')
        ],
        '15avg': [
            (0, 'REPLACE_ME'),
            (20, 'good'), (40, 'degraded'),
            (60, '#ffa500'), (80, 'bad')
        ],
    }
}

# don't show load averages if 1avg is under 60%
loadavg {
    format = '[\?if=1avg>59 Loadavg [\?color=1avg {1min}] '
    format += '[\?color=5avg {5min}] [\?color=15avg {15min}]]'
}

# add your snippets here
loadavg {
    format = "..."
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'Loadavg '},
    {'full_text': '2.73 1.84 1.34', 'color': '#9dd7fb'},
]

detailed
[
    {'full_text': '1min ', 'color': '#a9a9a9'},
    {'full_text': '0.48', 'color': '#9DD7FB'},
    {'full_text': '|', 'color': '#a9a9a9'},
    {'full_text': '4.0%', 'color': '#9DD7FB'},
    {'full_text': ' 5min ', 'color': '#a9a9a9'},
    {'full_text': '0.51', 'color': '#9DD7FB'},
    {'full_text': '|', 'color': '#a9a9a9'},
    {'full_text': '4.2%', 'color': '#9DD7FB'},
    {'full_text': ' 15min ', 'color': '#a9a9a9'},
    {'full_text': '0.54', 'color': '#9DD7FB'},
    {'full_text': '|', 'color': '#a9a9a9'},
    {'full_text': '4.5%', 'color': '#9DD7FB'}
]

percentages
[
    {'full_text': 'percentages '},
    {'full_text': '65.1% ', 'color': '#ffa500'},
    {'full_text': '44.8% ', 'color': '#ffff00'},
    {'full_text': '25.0%', 'color': '#00ff00'},
]

shadesofgrey
[
    {'full_text': 'shades_of_grey '},
    {'full_text': '0.49 ', 'color': '#dddddd'},
    {'full_text': '0.70 ', 'color': '#bbbbbb'},
    {'full_text': '0.89', 'color': '#999999'},
]

shadesofblue
[
    {'full_text': 'shades_of_blue '},
    {'full_text': '0.88 ', 'color': '#87cefa'},
    {'full_text': '0.92 ', 'color': '#35adf7'},
    {'full_text': '0.91', 'color': '#0983cf'},
]

monochrome
[
    {'full_text': 'monochrome '},
    {'full_text': '0.41 ', 'color': '#9dd7fb'},
    {'full_text': '0.75 0.85'},
]

htop
[
    {'full_text': 'htop '},
    {'full_text': '1.64 ', 'color': '#9dd7fb'},
    {'full_text': '1.68 ', 'color': '#00ffff'},
    {'full_text': '1.67', 'color': '#008b8b'},
]

black_night
[
    {'full_text': 'black_night '},
    {'full_text': '0.51 ', 'color': '#adff2f'},
    {'full_text': '1.01 0.93', 'color': '#32cd32'},
]

orange_gold
[
    {'full_text': 'orange_gold '},
    {'full_text': '0.51 ', 'color': '#ffa500'},
    {'full_text': '1.01 0.93', 'color': '#ffd700'},
]
"""

from os import getloadavg
from multiprocessing import cpu_count


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = (
        "Loadavg [\?color=1avg {1min}] " "[\?color=5avg {5min}] [\?color=15avg {15min}]"
    )
    thresholds = [
        (0, "#9dd7fb"),
        (20, "good"),
        (40, "degraded"),
        (60, "#ffa500"),
        (80, "bad"),
    ]

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {
                        "1min": ":.2f",
                        "5min": ":.2f",
                        "15min": ":.2f",
                        "1avg": ":.1f",
                        "5avg": ":.1f",
                        "15avg": ":.1f",
                    },
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        self.load_data = {}
        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def loadavg(self):
        cpu = float(cpu_count())

        for key, value in zip(["1", "5", "15"], getloadavg()):
            self.load_data[key + "min"] = value
            self.load_data[key + "avg"] = value / cpu * 100

        for x in self.thresholds_init:
            if x in self.load_data:
                self.py3.threshold_get_color(self.load_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, self.load_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
