r"""
Display network speed and bandwidth usage.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 2)
    format: display format for this module
        *(default '{nic} [\?color=down LAN(Kb): {down}↓ {up}↑] '
        '[\?color=total T(Mb): {download}↓ {upload}↑ {total}↕]')*
    nic: specify a network interface to use (default None)
    thresholds: specify color thresholds to use
        *(default {'down': [(0, 'bad'), (30, 'degraded'), (60, 'good')],
        'total': [(0, 'good'), (400, 'degraded'), (700, 'bad')]})*

Format placeholders:
    {nic}      network interface
    {down}     number of download speed
    {up}       number of upload speed
    {download} number of download usage
    {upload}   number of upload usage
    {total}    number of total usage

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author Shahin Azad <ishahinism at Gmail>

SAMPLE OUTPUT
[
    {'full_text': 'eth0 '},
    {'full_text': 'LAN(Kb):  77.8↓  26.9↑ ', 'color': '#00FF00'},
    {'full_text': 'T(Mb): 394↓  45↑ 438↕', 'color': '#FFFF00'},
]
"""

import time
from pathlib import Path


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 2
    format = (
        r"{nic} [\?color=down LAN(Kb): {down}↓ {up}↑] "
        r"[\?color=total T(Mb): {download}↓ {upload}↑ {total}↕]"
    )
    nic = None
    thresholds = {
        "down": [(0, "bad"), (30, "degraded"), (60, "good")],
        "total": [(0, "good"), (400, "degraded"), (700, "bad")],
    }

    class Meta:
        def deprecate_function(config):
            return {
                "thresholds": {
                    "down": [
                        (0, "bad"),
                        (config.get("low_speed", 30), "degraded"),
                        (config.get("med_speed", 60), "good"),
                    ],
                    "total": [
                        (0, "good"),
                        (config.get("low_traffic", 400), "degraded"),
                        (config.get("med_traffic", 700), "bad"),
                    ],
                }
            }

        deprecated = {
            "function": [{"function": deprecate_function}],
            "remove": [
                {
                    "param": "low_speed",
                    "msg": "obsolete, set using thresholds parameter",
                },
                {
                    "param": "med_speed",
                    "msg": "obsolete, set using thresholds parameter",
                },
                {
                    "param": "low_traffic",
                    "msg": "obsolete, set using thresholds parameter",
                },
                {
                    "param": "med_traffic",
                    "msg": "obsolete, set using thresholds parameter",
                },
            ],
        }

        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {
                        "down": ":5.1f",
                        "up": ":5.1f",
                        "download": ":3.0f",
                        "upload": ":3.0f",
                        "total": ":3.0f",
                    },
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        self.last_transmitted_bytes = 0
        self.last_received_bytes = 0
        self.last_time = time.perf_counter()
        # Get default gateway from /proc.
        if self.nic is None:
            with Path("/proc/net/route").open() as fh:
                for line in fh:
                    fields = line.strip().split()
                    if fields[1] == "00000000" and int(fields[3], 16) & 2:
                        self.nic = fields[0]
                        break
            if self.nic is None:
                self.nic = "lo"
            self.py3.log(f"selected nic: {self.nic}")

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def _get_bytes(self):
        with Path("/proc/net/dev").open() as fh:
            net_data = fh.read().split()
        interface_index = net_data.index(self.nic + ":")
        received_bytes = int(net_data[interface_index + 1])
        transmitted_bytes = int(net_data[interface_index + 9])
        return received_bytes, transmitted_bytes

    def netdata(self):
        received_bytes, transmitted_bytes = self._get_bytes()
        # speed
        current_time = time.perf_counter()
        timedelta = current_time - self.last_time
        self.last_time = current_time
        down = (received_bytes - self.last_received_bytes) / 1024 / timedelta
        up = (transmitted_bytes - self.last_transmitted_bytes) / 1024 / timedelta
        # history
        self.last_received_bytes = received_bytes
        self.last_transmitted_bytes = transmitted_bytes
        # traffic
        download = received_bytes / 1024 / 1024
        upload = transmitted_bytes / 1024 / 1024
        total = download + upload

        net_data = {
            "down": down,
            "up": up,
            "download": download,
            "upload": upload,
            "total": total,
            "nic": self.nic,
        }

        for x in self.thresholds_init:
            if x in net_data:
                self.py3.threshold_get_color(net_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, net_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
