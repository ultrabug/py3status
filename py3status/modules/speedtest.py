# -*- coding: utf-8 -*-
"""
Do a bandwidth test with speedtest-cli.

Configuration parameters:
    button_share: button to open the result link (default None)
    format: display format for this module, {download} and/or {upload} required
        *(default 'Speedtest[\?color=darkgray  time [\?color=degraded {elapsed_time} s]]'
                    '[\?color=darkgray  ping [\?color=ping {ping} ms ]'
                    'up [\?color=upload {upload} {upload_unit}] '
                    'down [\?color=download {download} {download_unit}]]')*
    server_id: speedtest server to use, `speedtest-cli --list` to get id (default None)
    si_units: use SI units (default False)
    thresholds: specify color thresholds to use *(default {
                'download': [(0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')],
                'ping': [(200, 'bad'), (150, 'orange'), (100, 'degraded'), (10, 'good')],
                'upload': [(0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')]})*
    timeout: timeout when communicating with speedtest.net servers (default None)
    unit_bitrate: unit for download/upload rate (default 'MB/s')
    unit_size: unit for bytes_received/bytes_sent (default 'MB')

Format placeholders:
    {bytes_sent}            bytes sent during test, human readable, eg '52.45'
    {bytes_sent_unit}       unit used for bytes_sent, eg 'MB'
    {bytes_received}        bytes received during test, human readable, eg '70.23'
    {bytes_received_unit}   unit used for bytes_received, eg 'MB'
    {client_country}        client country code, eg 'FR'
    {client_ip}             client ip, eg '78.194.13.7'
    {client_isp}            client isp, eg 'Free SAS'
    {client_ispdlavg}       client isp download average, eg '0'
    {client_isprating}      client isp rating, eg 3.7
    {client_ispulavg}       client isp upload average, eg '0'
    {client_lat}            client latitude, eg '48.8534'
    {client_loggedin}       client logged in, eg '0'
    {client_lon}            client longitude, eg '2.3487999999999998'
    {client_rating}         client rating, eg '0'
    {download}              download rate from speedtest server, human readable
    {download_unit}         unit used as , eg 'MB/s'
    {elapsed_time}          elapsed time since speedtest start
    {ping}                  ping time in ms to speedtest server
    {timestamp}             timestamp of the run, eg '2018-08-30T16:27:25.318212Z'
    {server_cc}             server country code, eg 'FR'
    {server_country}        server country, eg 'France'
    {server_d}              server distance, eg '2.316599376968091'
    {server_host}           server host, eg 'speedtest.telecom-paristech.fr:8080'
    {server_id}             server id, eg '11977'
    {server_lat}            server latitude, eg '48.8742'
    {server_latency}        server latency, eg 8.265
    {server_lon}            server longitude, eg 2.3470
    {server_name}           server name, eg 'Paris'
    {server_sponsor}        server sponsor, eg 'Télécom ParisTech'
    {server_url}            server url, eg 'http://speedtest.telecom-paristech.fr/upload.php'
    {upload}                upload rate to speedtest server, human readable
    {upload_unit}           unit used for upload, eg 'MB/s'


Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

The module will be triggered on click only. Not at start.

Note that all placeholders have a version prefixed by `previous_`, eg `previous_download`.
This can be usefull to compare two runs.

Requires:
    speedtest-cli: Command line interface for testing internet bandwidth using speedtest.net

@author Cyril Levis (@cyrinux)

Examples:
```
# colored based on thresholds
speedtest {
    thresholds = {
        "download": [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")],
        "ping": [(200, "bad"), (150, "orange"), (100, "degraded"), (10, "good")],
        "upload": [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")],
    }
    format = '[\?color=ping {ping} ms] [\?color=upload Up {upload} {upload_unit}]'
    format += ' [\?color=download Down {download} {download_unit}]'
}

# colored based on comparation between two last runs
speedtest {
    format = '[[\?if=download<previous_download&color=degraded Faster]'
    format += '|[\?color=good Slower]]'
}

# compare only download
speedtest {
    format = '[[\?if=download<previous_download ↓ {download} {download_unit}]'
    format += '[\?if=download<previous_download ↑ {download} {download_unit}]'
    format += '[\?if=download=previous_download -> {download} {download_unit}]'
    format += '|speedtest'
}
```

SAMPLE OUTPUT
[
    {"full_text": "Speedtest " },
    {"full_text": "ping ", "color": "#a9a9a9"},
    {"full_text": "9.498 ms", "color": "#ebdbb2"},
    {"full_text": " up ", "color": "#a9a9a9"},
    {"full_text": "78.42 MB/s", "color": "#fb4934"},
    {"full_text": " down ", "color": "#a9a9a9"},
    {"full_text": "39.58 MB/s", "color": "#fb4934"}
]
"""

from json import loads
import threading
import time


STRING_NOT_INSTALLED = "not installed"


class SpeedtestCli(threading.Thread):
    """
    A thread running speedtest-cli
    """

    def __init__(self, parent):
        super(SpeedtestCli, self).__init__()
        self.parent = parent

    def run(self):
        self.parent._start()


class Py3status:
    """
    """

    class Meta:
        update_config = {
            'update_placeholder_format': [
                {
                    'placeholder_formats': {
                        'download': ':.1f',
                        'previous_download': ':.1f',
                        'upload': ':.1f',
                        'previous_upload': ':.1f',
                        'ping': ':.1f',
                        'elapsed_time': ':.0f',
                    },
                    'format_strings': ['format'],
                }
            ],
        }
    # available configuration parameters
    button_share = None
    format = (
        u"Speedtest[\?color=darkgray  time [\?color=degraded {elapsed_time} s]]"
        "[\?color=darkgray  ping [\?color=ping {ping} ms ]"
        "up [\?color=upload {upload} {upload_unit}] "
        "down [\?color=download {download} {download_unit}]]"
    )
    server_id = None
    si_units = False
    thresholds = {
        "download": [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")],
        "ping": [(200, "bad"), (150, "orange"), (100, "degraded"), (10, "good")],
        "upload": [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")],
    }
    timeout = None
    unit_bitrate = "MB/s"
    unit_size = "MB"

    def post_config_hook(self):
        if not self.py3.check_commands("speedtest-cli"):
            raise Exception(STRING_NOT_INSTALLED)

        self.button_refresh = 2
        self.cached_until = self.py3.CACHE_FOREVER
        self.command = "speedtest-cli --json --secure"
        self.placeholders = self.py3.get_placeholders_list(self.format)
        self.speedtest_data = {}
        self.start_time = None
        self.thresholds_init = self.py3.get_color_names_list(self.format)
        self.url = None

        tests = ["download", "upload"]
        # if download* or upload* missing, run complete test
        if any(x in tests for x in self.placeholders):
            if "upload" not in self.placeholders:
                self.command += " --no-upload"

            if "download" not in self.placeholders:
                self.command += " --no-download"

        if self.server_id:
            self.command += " --server {}".format(self.server_id)

        if self.timeout:
            self.command += " --timeout {}".format(self.timeout)

        if self.button_share and all(x in self.placeholders for x in tests):
            self.command += " --share"

    def _is_running(self):
        try:
            self.py3.command_output(["pgrep", "speedtest-cli"])
            return True
        except self.py3.CommandError:
            return False

    def _cast_number(self, value):
        try:
            value = float(value)
        except ValueError:
            try:
                value = int(value)
            except ValueError:
                pass
        return value

    def _get_speedtest_data(self):
        try:
            return loads(self.py3.command_output(self.command))
        except self.py3.CommandError:
            return None

    def _start(self):
        # do nothing if allready running
        if self._is_running():
            return

        # start timer
        self.start_time = time.time()

        # get values
        previous_data = self.py3.storage_get("speedtest_data") or {}
        current_data = self._get_speedtest_data()

        # zero-ing if not fetched and units convertion
        for x in ["download", "upload", "bytes_received", "bytes_sent"]:
            unit = self.unit_size if "bytes" in x else self.unit_bitrate
            current_data[x] = current_data.get(x, 0)
            current_data[x], current_data[x + "_unit"] = self.py3.format_units(
                current_data[x], unit=unit, si=self.si_units
            )

        # extra data, not sure we want to expose
        current_data = self.py3.flatten_dict(current_data, delimiter='_')

        # store last data fetched
        self.py3.storage_set("speedtest_data", current_data)

        # get speedtest result url
        self.url = current_data.get("share")

        # create placeholders
        self.speedtest_data.update(current_data)
        self.speedtest_data.update(
            {"previous_" + k: v for (k, v) in previous_data.items()}
        )

        # stop timer / stop refreshing
        self.start_time = None
        self.cached_until = self.py3.CACHE_FOREVER

        # cast number
        self.speedtest_data.update(
            {
                k: self._cast_number(self.speedtest_data[k])
                for k in self.placeholders
            }
        )

        # thresholds
        for x in self.thresholds_init:
            if x in self.speedtest_data:
                self.py3.threshold_get_color(self.speedtest_data[x], x)

    def speedtest(self):
        # calculate elapsed time since start
        elapsed_time = None
        if self.start_time:
            elapsed_time = self._cast_number(time.time() - self.start_time)
            self.py3.log(type(elapsed_time))
        self.speedtest_data['elapsed_time'] = elapsed_time

        return {
            "cached_until": self.cached_until,
            "full_text": self.py3.safe_format(self.format, self.speedtest_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_share and self.url:
            self.py3.command_run("xdg-open %s" % self.url)
        if button == self.button_refresh:
            # start speedtest-cli thread
            # dont cache while thread working
            SpeedtestCli(self).start()
            self.cached_until = self.py3.time_in(0)
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
