# -*- coding: utf-8 -*-
"""
Do a bandwidth test with speedtest-cli.

Configuration parameters:
    cache_timeout: refresh interval for this module (default -1)
    format: display format for this module (default '■ [{ping} ms] [↑ {upload}] [↓ {download}]')
    si_units: use SI units (default False)
    sleep_timeout: when speedtest-cli is allready running, this interval will be used
        to allow faster retry refreshes
        (default 20)
    timeout: timeout when communicating with speedtest.net servers (default 10)
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (11, 'good')])
    unit_bitrate: unit for download/upload rate (default 'MB/s')
    unit_size: unit for bytes_received/bytes_sent (default 'MB')

Format placeholders:
    {download} download rate from speedtest server, human readable
    {download_raw} download rate from speedtest server, for format comparation
    {download_unit} unit used as , eg 'MB/s'
    {ping} ping time in ms to speedtest server
    {upload} upload rate to speedtest server, human readable
    {upload_raw} upload rate to speedtest server, for format comparation
    {upload_unit} unit used for upload, eg 'MB/s'
    {bytes_sent} bytes sent during test, human readable
    {bytes_sent_unit} unit used for bytes_sent, eg 'MB'
    {bytes_sent_raw} bytes sent during test, for format comparation
    {bytes_received} bytes received during test, human readable
    {bytes_received_raw} bytes received during test, for format comparation
    {bytes_received_unit} unit used for bytes_received, eg 'MB'
    {timestamp} timestamp of the run

The module will be triggered on clic only. Not at start.

Note that all placeholders have a version prefixed by `previous_`, eg `previous_download`.
This can be usefull to compare two runs.

Requires:
    speedtest-cli: Command line interface for testing internet bandwidth using speedtest.net

Examples:
```
# colored based on thresholds
speedtest_cli {
    thresholds = {
        'ping': [
            (200, 'bad'), (150, 'orange'), (100, 'degraded'), (10, 'good')
        ],
        'download': [
            (0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')
        ],
        'upload': [
            (0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')
        ],
    }
    format = '[\?color=ping {ping} ms] [\?color=upload ↑ {upload} {upload_unit}]'
    format += ' [\?color=download ↓ {download} {download_unit}]'
}


# colored based on comparation between two last runs
speedtest_cli {
    format = ' [[\?if=download_raw<previous_download_raw&color=degraded ↓]|[\?color=ok ↑]]'
}

@author Cyril Levis (@cyrinux)

SAMPLE OUTPUT
{'full_text': u'\u25cf 208.18 ms \u2191 0.247 MB/s \u2193 0.453 MB/s'}
"""

from __future__ import division  # python2 compatibility
from json import loads

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = -1
    format = (
        u"\u25cf [{ping} ms] [↑ {upload} {upload_unit}] [↓ {download} {download_unit}]"
    )
    si_units = False
    sleep_timeout = 20
    thresholds = {
        "ping": [(200, "bad"), (150, "orange"), (100, "degraded"), (10,
                                                                    "good")],
        "download": [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")],
        "upload": [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")],
        "speed" [("good", "good"), ("slower", "degraded"), ("faster","good")],
    }
    unit_bitrate = "MB/s"
    unit_size = "MB"
    timeout = 30

    def post_config_hook(self):
        if not self.py3.check_commands("speedtest-cli"):
            raise Exception(STRING_NOT_INSTALLED)

        self.placeholders = list(
            set(self.py3.get_placeholders_list(self.format)))
        self.can_refresh = False
        self.speedtest_command = "speedtest-cli --json --secure --timeout {}".format(
            self.timeout)

        # avoid bad behavior if speedtest timeout greater than cache_timeout
        if self.cache_timeout < self.timeout and self.cache_timeout != -1:
            self.cache_timeout = self.timeout + 5

    def _is_running(self):
        try:
            self.py3.command_output(["pgrep", "speedtest-cli"])
            return True
        except:
            return False

    def _get_speedtest_data(self):
        data = {}
        try:
            data = loads(self.py3.command_output(self.speedtest_command))
            self.py3.log(data)
        except self.py3.CommandError as ce:
            self.py3.log(ce.output)
            return ce.output
        return data

    def speedtest_cli(self):
        current_data = {}
        speedtest_data = {}
        previous_data = {}
        cached_until = self.sleep_timeout

        if not self._is_running() and self.can_refresh:
            previous_data = self.py3.storage_get("speedtest_data")
            current_data = self._get_speedtest_data()
            cached_until = self.cache_timeout

            if current_data and len(current_data) > 1:
                # create a "total" for know if cnx is better or not
                # between two run
                current_data["total"] = int(current_data.get(
                    "download", 0)) + int(current_data.get("upload", 0))

                if "total" in previous_data:
                    if current_data["total"] >= previous_data["total"]:
                        current_data["speed"] = "faster"
                    else:
                        current_data["speed"] = "slower"
                else:
                    current_data["speed"] = "good"

        # zero-ing if not fetched, raw version and units convertion
        for x in ["download", "upload"]:
            current_data[x] = current_data.get(x, 0)
            current_data[x + "_raw"] = current_data[x]
            current_data[x], current_data[x + "_unit"] = self.py3.format_units(
                current_data[x], unit=self.unit_bitrate, si=self.si_units)

        for x in ["bytes_received", "bytes_sent"]:
            current_data[x] = current_data.get(x, 0)
            current_data[x + "_raw"] = current_data[x]
            current_data[x], current_data[x + "_unit"] = self.py3.format_units(
                current_data[x], unit=self.unit_size, si=self.si_units)

        # store last data fetched
        self.py3.storage_set("speedtest_data", current_data)

        # create placeholders
        for x in current_data:
            speedtest_data[x] = current_data[x]
        for x in previous_data:
            speedtest_data["previous_" + x] = previous_data[x]

        # thresholds
        for x in self.thresholds:
            if x in speedtest_data:
                self.py3.threshold_get_color(speedtest_data[x], x)

        self.py3.log(speedtest_data)

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, speedtest_data),
        }

    def on_click(self, event):
        # little hack for prevent running speedtest
        # at start, allow only trigger on_click / refresh
        self.can_refresh = True
        if self._is_running:
            self.py3.prevent_refresh()
        else:
            pass


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
