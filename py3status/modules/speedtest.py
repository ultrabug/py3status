# -*- coding: utf-8 -*-
"""
Do a bandwidth test with speedtest-cli.

Configuration parameters:
    button_share: button to open the result link (default None)
    format: display format for this module, {download} and/or {upload} required
        *(default 'Speedtest [\?color=darkgray ping [\?color=ping {ping} ms] '
                    'up [\?color=upload {upload} {upload_unit}] '
                    'down [\?color=download {download} {download_unit}]]')*
    server_id: speedtest server to use, `speedtest-cli --list` to get id (default None)
    si_units: use SI units (default False)
    thresholds: specify color thresholds to use *(default {
                'download': [(0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')],
                'ping': [(200, 'bad'), (150, 'orange'), (100, 'degraded'), (10, 'good')],
                'upload': [(0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')]})*
    timeout: timeout when communicating with speedtest.net servers (default 10)
    unit_bitrate: unit for download/upload rate (default 'MB/s')
    unit_size: unit for bytes_received/bytes_sent (default 'MB')

Format placeholders:
    {bytes_sent}            bytes sent during test, human readable, eg '52.45'
    {bytes_sent_unit}       unit used for bytes_sent, eg 'MB'
    {bytes_sent_raw}        bytes sent during test, for format comparation, eg '52445184.0'
    {bytes_received}        bytes received during test, human readable, eg '70.23'
    {bytes_received_raw}    bytes received during test, for format comparation, eg '70229556.0'
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
    {download_raw}          download rate from speedtest server, for format comparation
    {download_unit}         unit used as , eg 'MB/s'
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
    {upload_raw}            upload rate to speedtest server, for format comparation
    {upload_unit}           unit used for upload, eg 'MB/s'

Color thresholds:
    field_name: print a color based on the value of `field_name` placeholder

The module will be triggered on clic only. Not at start.

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
    format = '[[\?if=download_raw<previous_download_raw&color=degraded Faster]'
    format += '|[\?color=ok Slower]]'
}

# compare only download
speedtest {
    format = '[[\?if=download_raw<previous_download_raw ↓ {download} {download_unit}]'
    format += '[\?if=download_raw>previous_download_raw ↑ {download} {download_unit}]'
    format += '[\?if=download_raw=previous_download_raw -> {download} {download_unit}]'
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
from numbers import Number

STRING_NOT_INSTALLED = "not installed"
MISSING_PLACEHOLDER = "{download} or {upload} placeholder required"


class Py3status:
    """
    """

    # available configuration parameters
    button_share = None
    format = (
        u"Speedtest [\?color=darkgray ping [\?color=ping {ping} ms] "
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
    timeout = 10
    unit_bitrate = "MB/s"
    unit_size = "MB"

    def post_config_hook(self):
        if not self.py3.check_commands("speedtest-cli"):
            raise Exception(STRING_NOT_INSTALLED)

        self.button_refresh = 2
        self.sleep_timeout = 2.5
        self.speedtest_data = {}
        self.cached_until = self.py3.CACHE_FOREVER
        self.placeholders = self.py3.get_placeholders_list(self.format)
        self.thresholds_init = self.py3.get_color_names_list(self.format)
        self.command = "speedtest-cli --json --secure"
        self.url = None

        # if download* or upload* missing, run complete test
        if any(
            key.startswith(x)
            for x in ["download", "upload"]
            for key in self.placeholders
        ):
            if not any(key.startswith("upload") for key in self.placeholders):
                self.command += " --no-upload"

            if not any(key.startswith("download") for key in self.placeholders):
                self.command += " --no-download"

        if self.server_id and int(self.server_id):
            self.command += " --server " + str(self.server_id)

        if self.button_share and all(
            x in self.placeholders for x in ["download", "upload"]
        ):
            self.command += " --share"

        self.command += " --timeout " + str(self.timeout)

    def _is_running(self):
        try:
            self.py3.command_output(["pgrep", "speedtest-cli"])
            return True
        except self.py3.CommandError:
            return False

    def _cast_number(self, value):
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
        return value

    def _get_speedtest_data(self):
        return loads(self.py3.command_output(self.command))

    def _start(self):
        self.cached_until = self.py3.time_in(self.sleep_timeout)

        if not self._is_running():
            self.cached_until = self.py3.CACHE_FOREVER
            previous_data = self.py3.storage_get("speedtest_data") or {}
            current_data = self._get_speedtest_data() or {}

            if len(current_data) > 1:
                # create a "total" for know if cnx is better or not
                # between two run
                current_data["total"] = int(current_data.get("download", 0)) + int(
                    current_data.get("upload", 0)
                )

        # zero-ing if not fetched, raw version and units convertion
        for x in ["download", "upload", "bytes_received", "bytes_sent"]:
            unit = self.unit_size if "bytes" in x else self.unit_bitrate
            current_data[x] = current_data.get(x, 0)
            current_data[x + "_raw"] = current_data[x]
            current_data[x], current_data[x + "_unit"] = self.py3.format_units(
                current_data[x], unit=unit, si=self.si_units
            )

        # extra data, not sure we want to expose
        current_data = self.py3.flatten_dict(
            current_data, delimiter='_', intermediates=False
        )

        # store last data fetched
        self.py3.storage_set("speedtest_data", current_data)

        # get speedtest result url
        self.url = current_data.get("share")

        # create placeholders
        self.speedtest_data.update(current_data)
        self.speedtest_data.update(
            {"previous_" + k: v for (k, v) in previous_data.items()}
        )

        # cast number
        self.speedtest_data.update(
            {
                k: self._cast_number(self.speedtest_data[k])
                for k in self.placeholders if isinstance(
                    self.speedtest_data[k], Number
                )
            }
        )

        # thresholds
        for x in self.thresholds_init:
            if x in self.speedtest_data:
                self.py3.threshold_get_color(self.speedtest_data[x], x)

    def speedtest(self):
        return {
            "cached_until": self.cached_until,
            "full_text": self.py3.safe_format(self.format, self.speedtest_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_share and self.url:
            self.py3.command_run("xdg-open %s" % self.url)
        if button != self.button_refresh:
            self.py3.prevent_refresh()
        if button == self.button_refresh:
            self._start()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
