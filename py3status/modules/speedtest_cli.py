# -*- coding: utf-8 -*-
"""
Do a bandwidth test with speedtest-cli.

Configuration parameters:
    button_refresh: button to run the check (default 2)
    button_share: button to open the result link (default None)
    format: display format for this module, {download} and/or {upload} required
        (default '● [{ping} ms] [↑ {upload} {upload_unit}] [↓ {download} {download_unit}]')
    server_id: speedtest server to use, `speedtest-cli --list` to get id (default None)
    si_units: use SI units (default False)
    sleep_timeout: when speedtest-cli is allready running, this interval will be used
        to allow faster retry refreshes (default 5)
    thresholds: specify color thresholds to use (default [
                'download': [(0, 'bad'), (1024, 'degraded'), (1048576, 'good')],
                'ping': [(200, 'bad'), (150, 'orange'), (100, 'degraded'), (10, 'good')],
                'quality':
                    [
                        ('ok', 'good'), ('bad', 'degraded'),
                        ('faster', 'good'), ('slower', 'degraded'), ('faster', 'good')
                    ],
                'upload': [(0, 'bad'), (1024, 'degraded'), (1048576, 'good')]
        ])
    timeout: timeout when communicating with speedtest.net servers (default 10)
    unit_bitrate: unit for download/upload rate (default 'MB/s')
    unit_size: unit for bytes_received/bytes_sent (default 'MB')

Format placeholders:
    {bytes_sent} bytes sent during test, human readable
    {bytes_sent_unit} unit used for bytes_sent, eg 'MB'
    {bytes_sent_raw} bytes sent during test, for format comparation
    {bytes_received} bytes received during test, human readable
    {bytes_received_raw} bytes received during test, for format comparation
    {bytes_received_unit} unit used for bytes_received, eg 'MB'
    {client_country} client country code, eg 'FR'
    {client_ip} client ip, eg '78.194.13.7'
    {client_isp} client isp, eg 'Free SAS'
    {client_ispdlavg} client isp download average, eg '0'
    {client_isprating} client isp rating, eg 3.7
    {client_ispulavg} client isp upload average, eg '0'
    {client_lat} client latitude, eg '48.8534'
    {client_loggedin} client logged in, eg '0'
    {client_lon} client longitude, eg '2.3487999999999998'
    {client_rating} client rating, eg '0'
    {download} download rate from speedtest server, human readable
    {download_raw} download rate from speedtest server, for format comparation
    {download_unit} unit used as , eg 'MB/s'
    {ping} ping time in ms to speedtest server
    {quality} quality of the connection, eg ok, bad, faster, slower
    {timestamp} timestamp of the run
    {server_cc} server country code, eg 'FR'
    {server_country} server country, eg 'France'
    {server_d} server distance, eg '2.316599376968091'
    {server_host} server host, eg 'speedtest.telecom-paristech.fr:8080'
    {server_id} server id, eg '11977'
    {server_lat} server latitude, eg '48.8742'
    {server_latency} server latency, eg 8.265
    {server_lon} server longitude, eg 2.3470
    {server_name} server name, eg 'Paris'
    {server_sponsor} server sponsor, eg 'Télécom ParisTech'
    {server_url} server url, eg 'http://speedtest.telecom-paristech.fr/upload.php'
    {upload} upload rate to speedtest server, human readable
    {upload_raw} upload rate to speedtest server, for format comparation
    {upload_unit} unit used for upload, eg 'MB/s'

Color thresholds:
    format:
        xxx: print a color based on the value of `xxx` placeholder

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
        'download': [
            (0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')
        ],
        'ping': [
            (200, 'bad'), (150, 'orange'), (100, 'degraded'), (10, 'good')
        ],
        'quality': [
            ("ok", "good"),
            ("bad", "degraded"),
            ("faster", "good"),
            ("slower", "degraded"),
            ("faster", "good"),
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

# compare only download
speedtest_cli {
    format = '[[\?if=quality=slower&color=download ↓ {download} {download_unit}]'
    format += '[\?if=quality=faster&color=download ↑ {download} {download_unit}]'
    format += '[\?if=quality=ok&color=download -> {download} {download_unit}]'
    format += '[\?if=quality=bad&color=download x {download} {download_unit}]]'
    format += '|'
}
```

@author Cyril Levis (@cyrinux)

SAMPLE OUTPUT
{'full_text': u'\u25cf 208.18 ms \u2191 0.247 MB/s \u2193 0.453 MB/s'}
"""

from json import loads

STRING_NOT_INSTALLED = "not installed"
MISSING_PLACEHOLDER = "{download} or {upload} placeholder required"


class Py3status:
    """
    """

    # available configuration parameters
    button_refresh = 2
    button_share = None
    format = (
        u"\u25cf [{ping} ms] [↑ {upload} {upload_unit}] [↓ {download} {download_unit}]"
    )
    server_id = None
    si_units = False
    sleep_timeout = 5
    thresholds = {
        "download": [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")],
        "ping": [(200, "bad"), (150, "orange"), (100, "degraded"), (10, "good")],
        "quality": [
            ("ok", "good"),
            ("bad", "degraded"),
            ("faster", "good"),
            ("slower", "degraded"),
            ("faster", "good"),
        ],
        "upload": [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")],
    }
    timeout = 10
    unit_bitrate = "MB/s"
    unit_size = "MB"

    def post_config_hook(self):
        if not self.py3.check_commands("speedtest-cli"):
            raise Exception(STRING_NOT_INSTALLED)

        # fail if download or upload missing
        if not any(x in ["download", "upload"] for x in self.placeholders):
            raise Exception("%s" % (MISSING_PLACEHOLDER))

        self.first_run = True
        self.placeholders = self.py3.get_placeholders_list(self.format)

        dont_upload = ""
        if "upload" not in self.placeholders:
            dont_upload = "--no-upload"

        dont_download = ""
        if "download" not in self.placeholders:
            dont_download = "--no-download"

        server = ""  # if not specified, nearest server is use
        if self.server_id and int(self.server_id):
            server = "--server {}".format(self.server_id)

        share = ""
        if self.button_share and all(
            x in self.placeholders for x in ["download", "upload"]
        ):
            share = "--share"

        self.command = "speedtest-cli --json --secure --timeout {} {} {} {} {}".format(
            self.timeout, dont_upload, dont_download, server, share
        )

    def _is_running(self):
        try:
            self.py3.command_output(["pgrep", "speedtest-cli --json"])
            return True
        except:
            return False

    def _get_speedtest_data(self):
        return loads(self.py3.command_output(self.command)) or None

    def speedtest_cli(self):
        speedtest_data = {}
        if self.first_run:
            self.first_run = False
            cached_until = self.py3.time_in(0)
        else:
            current_data = {}
            previous_data = {}
            cached_until = self.py3.time_in(self.sleep_timeout)
            if self.first_run:
                self.first_run = False

            if not self._is_running():
                previous_data = self.py3.storage_get("speedtest_data")
                current_data = self._get_speedtest_data()
                cached_until = self.py3.CACHE_FOREVER

                if current_data and len(current_data) > 1:
                    # create a "total" for know if cnx is better or not
                    # between two run
                    current_data["total"] = int(current_data.get("download", 0)) + int(
                        current_data.get("upload", 0)
                    )

                    # create "quality" #maybe bad name
                    if "total" in previous_data:
                        if current_data["total"] >= previous_data["total"]:
                            quality = "faster"
                        else:
                            quality = "slower"
                    else:
                        if current_data["total"] <= 0:
                            quality = "bad"
                        else:
                            quality = "ok"
                    current_data["quality"] = quality

            # zero-ing if not fetched, raw version and units convertion
            for x in ["download", "upload"]:
                current_data[x] = current_data.get(x, 0)
                current_data[x + "_raw"] = current_data[x]
                current_data[x], current_data[x + "_unit"] = self.py3.format_units(
                    current_data[x], unit=self.unit_bitrate, si=self.si_units
                )

            for x in ["bytes_received", "bytes_sent"]:
                current_data[x] = current_data.get(x, 0)
                current_data[x + "_raw"] = current_data[x]
                current_data[x], current_data[x + "_unit"] = self.py3.format_units(
                    current_data[x], unit=self.unit_size, si=self.si_units
                )

            # extra data, not sure we want to expose
            for x in ["server", "client"]:
                if x in current_data:
                    for y in current_data[x]:
                        current_data[x + "_" + y] = current_data[x][y]
                    del current_data[x]

            # store last data fetched
            self.py3.storage_set("speedtest_data", current_data)

            # get speedtest result url
            if "share" in current_data:
                self.url = current_data["share"]

            # create placeholders
            for x in current_data:
                speedtest_data[x] = current_data[x]
            for x in previous_data:
                speedtest_data["previous_" + x] = previous_data[x]

            # thresholds
            for x in self.thresholds:
                if x in speedtest_data:
                    self.py3.threshold_get_color(speedtest_data[x], x)

        return {
            "cached_until": cached_until,
            "full_text": self.py3.safe_format(self.format, speedtest_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_share and self.url:
            self.py3.command_run("xdg-open %s" % self.url)
        elif button != self.button_refresh:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
