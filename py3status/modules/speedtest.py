# -*- coding: utf-8 -*-
"""
Perform a bandwidth test with speedtest-cli.

Configuration parameters:
    button_share: mouse button to share an URL (default None)
    format: display format for this module
        *(default "speedtest[\?if=elapsed&color=elapsed_time  "
        "{elapsed_time}s][ [\?color=download ↓{download}Mbps] "
        "[\?color=upload ↑{upload}Mbps]]")*
    thresholds: specify color thresholds to use
        *(default {"upload": [(0, "violet")], "ping": [(0, "#fff381")],
        "download": [(0, "cyan")], "elapsed_time": [(0, "#1cbfff")]})*

Control placeholders:
    {elapsed}          elapsed time state, eg False, True

Format placeholders:
    {bytes_sent}       bytes sent during test (in MB), eg 52.45
    {bytes_received}   bytes received during test (in MB), eg 70.23
    {client_country}   client country code, eg FR
    {client_ip}        client ip, eg 78.194.13.7
    {client_isp}       client isp, eg Free SAS
    {client_ispdlavg}  client isp download average, eg 0
    {client_isprating} client isp rating, eg 3.7
    {client_ispulavg}  client isp upload average, eg 0
    {client_lat}       client latitude, eg 48.8534
    {client_loggedin}  client logged in, eg 0
    {client_lon}       client longitude, eg 2.3487999999999998
    {client_rating}    client rating, eg 0
    {download}         download speed (in MB), eg 20.23
    {elapsed_time}     elapsed time since speedtest start
    {ping}             ping time in ms to speedtest server
    {server_cc}        server country code, eg FR
    {server_country}   server country, eg France
    {server_d}         server distance, eg 2.316599376968091
    {server_host}      server host, eg speedtest.telecom-paristech.fr:8080
    {server_id}        server id, eg 11977
    {share}            share, eg share url
    {timestamp}        timestamp, eg 2018-08-30T16:27:25.318212Z
    {server_lat}       server latitude, eg 48.8742
    {server_latency}   server latency, eg 8.265
    {server_lon}       server longitude, eg 2.3470
    {server_name}      server name, eg Paris
    {server_sponsor}   server sponsor, eg Télécom ParisTech
    {server_url}       server url, eg http://speedtest.telecom-paristech...
    {upload}           upload speed (in MB), eg 20.23

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    speedtest-cli: Command line interface for testing Internet bandwidth

Examples:
```
# show detailed elapsed_time|download/upload
speedtest {
    format = "speedtest[\?soft  ][\?if=elapsed [\?color=darkgray [time "
    format += "[\?color=elapsed_time {elapsed_time} s]]]|[\?color=darkgray "
    # format += "ping [\?color=ping {ping} ms] "
    format += "download [\?color=download {download}Mbps] "
    format += "upload [\?color=upload {upload}Mbps]]]"
}

# show everything
speedtest {
    format = "speedtest[\?soft  ][\?color=darkgray "
    format += "[time [\?color=elapsed_time {elapsed_time} s]][\?soft  ]"
    format += "[ping [\?color=ping {ping} ms] "
    format += "download [\?color=download {download}Mbps] "
    format += "upload [\?color=upload {upload}Mbps]]]"
}

# minimal
speedtest {
    format = "speedtest[\?soft  ][\?if=elapsed "
    format += "[\?color=elapsed_time {elapsed_time}]|"
    # format += "[\?color=ping {ping}] "
    format += "[[\?color=download {download}] [\?color=upload {upload}]]]"
}

# don't hide data on reset
speedtest {
    format = "speedtest[\?soft  ][\?color=darkgray time "
    format += "[\?color=elapsed_time {elapsed_time} s] "
    # format += "ping [\?color=ping {ping} ms] "
    format += "download [\?color=download {download}Mbps] "
    format += "upload [\?color=upload {upload}Mbps]]"
}

# don't hide data on reset, minimal
speedtest {
    format = "speedtest[\?soft  ][[\?color=elapsed_time {elapsed_time}] "
    # format += "[\?color=ping {ping}] "
    format += "[\?color=download {download}] [\?color=upload {upload}]]"
}
```

@author Cyril Levis (@cyrinux)

SAMPLE OUTPUT
[
    {"full_text": "speedtest "},
    {"full_text": "19.76Mbps ", "color": "#00ffff"},
    {"full_text": "3.86Mbps", "color": "#ee82ee"},
]

time+ping
[
    {"full_text": "speedtest "},
    {"full_text": "time ", "color": "#a9a9a9"},
    {"full_text": "24.65 s ", "color": "#1cbfff"},
    {"full_text": "ping ", "color": "#a9a9a9"},
    {"full_text": "28.27 ms", "color": "#ffff00"},
]

details
[
    {"full_text": "speedtest "},
    {"full_text": "download ", "color": "#a9a9a9"},
    {"full_text": "18.2Mbps ", "color": "#00ffff"},
    {"full_text": "upload ", "color": "#a9a9a9"},
    {"full_text": "19.2Mbps", "color": "#ee82ee"},
]
"""

from json import loads
from threading import Thread
from time import time

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    button_share = None
    format = (
        u"speedtest[\?if=elapsed&color=elapsed_time  "
        u"{elapsed_time}s][ [\?color=download ↓{download}Mbps] "
        u"[\?color=upload ↑{upload}Mbps]]"
    )
    thresholds = {
        "download": [(0, "cyan")],
        "elapsed_time": [(0, "#1cbfff")],
        "ping": [(0, "#fff381")],
        "upload": [(0, "violet")],
    }

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "format_strings": ["format"],
                    "placeholder_formats": {
                        "bytes_received": ":.2f",
                        "bytes_sent": ":.2f",
                        "download": ":.2f",
                        "elapsed_time": ":.2f",
                        "ping": ":.2f",
                        "server_d": ":.2f",
                        "upload": ":.2f",
                    },
                }
            ]
        }

    def post_config_hook(self):
        self.speedtest_command = "speedtest-cli --json --secure"
        if not self.py3.check_commands(self.speedtest_command.split()[0]):
            raise Exception(STRING_NOT_INSTALLED)

        # init
        self.button_refresh = 2
        self.placeholders = self.py3.get_placeholders_list(self.format)
        self.speedtest_data = self.py3.storage_get("speedtest_data") or {}
        self.thread = None
        self.thresholds_init = self.py3.get_color_names_list(self.format)

        # remove elapsed_time
        if "elapsed_time" in self.placeholders:
            self.placeholders.remove("elapsed_time")

        # share
        if self.button_share:
            self.speedtest_command += " --share"

        # perform download/upload based on placeholders
        tests = ["download", "upload"]
        if any(x in tests for x in self.placeholders):
            for x in tests:
                if x not in self.placeholders:
                    self.speedtest_command += " --no-{}".format(x)

    def _set_speedtest_data(self):
        # start
        self.start_time = time()
        self.speedtest_data["elapsed"] = True

        try:
            self.speedtest_data = self.py3.flatten_dict(
                loads(self.py3.command_output(self.speedtest_command)), delimiter="_"
            )
            for x in ["download", "upload", "bytes_received", "bytes_sent"]:
                if x not in self.placeholders or x not in self.speedtest_data:
                    continue
                si = False if "bytes" in x else True
                self.speedtest_data[x], unit = self.py3.format_units(
                    self.speedtest_data[x], unit="MB", si=si
                )
        except self.py3.CommandError:
            pass

        # end
        self.speedtest_data["elapsed"] = False
        self.speedtest_data["elapsed_time"] = time() - self.start_time

    def speedtest(self):
        if self.speedtest_data.get("elapsed"):
            cached_until = 0
            self.speedtest_data["elapsed_time"] = time() - self.start_time
        else:
            cached_until = self.py3.CACHE_FOREVER
            self.py3.storage_set("speedtest_data", self.speedtest_data)

        # thresholds
        for x in self.thresholds_init:
            if x in self.speedtest_data:
                self.py3.threshold_get_color(self.speedtest_data[x], x)

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, self.speedtest_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_share:
            share = self.speedtest_data.get("share")
            if share:
                self.py3.command_run("xdg-open {}".format(share))
        if button == self.button_refresh:
            if self.thread and not self.thread.isAlive():
                self.thread = None
            if self.thread is None:
                self.thread = Thread(target=self._set_speedtest_data)
                self.thread.daemon = True
                self.thread.start()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
