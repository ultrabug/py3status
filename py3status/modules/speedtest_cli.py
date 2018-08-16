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
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (11, 'good')])

Format placeholders:
    {download} download rate from speedtest server (in MB/s)
    {ping} ping time in ms to speedtest server
    {upload} upload rate to speedtest server (in MB/s)
    {bytes_sent} bytes sent during test (in MB)
    {bytes_received} bytes received during test (in MB)

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
    format = '[\?color=ping {ping} ms] [\?color=upload ↑ {upload}] [\?color=download ↓ {download}]'
}

@author Cyril Levis (@cyrinux)

SAMPLE OUTPUT
{'full_text': u'\u25cf 208.18 ms \u2191 0.247 MB/s \u2193 0.453 MB/s'}
"""

from __future__ import division  # python2 compatibility
from json import loads

STRING_NOT_INSTALLED = 'not installed'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = -1
    format = u'\u25cf [{ping} ms] [↑ {upload}] [↓ {download}]'
    si_units = False
    sleep_timeout = 20
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

    def post_config_hook(self):
        if not self.py3.check_commands('speedtest-cli'):
            raise Exception(STRING_NOT_INSTALLED)

        self.placeholders = list(
            set(self.py3.get_placeholders_list(self.format))
        )
        self.speedtest_command = 'speedtest-cli --json --secure'

    def _is_running(self):
        try:
            self.py3.command_output(['pgrep', 'speedtest-cli'])
            return True
        except:
            return False

    def _get_speedtest_data(self):
        try:
            line = self.py3.command_output(self.speedtest_command)
        except self.py3.CommandError as ce:
            return ce.output

        if line:
            return loads(line)
        else:
            return None

    def _get_last_speedtest_data(self):
        new_data = {}
        last_data = self.py3.storage_get('speedtest_data')
        if last_data:
            for x in last_data:
                new_data['last_' + x] = last_data[x]
        return new_data

    def speedtest_cli(self):
        speedtest_data = {}
        cached_until = self.sleep_timeout

        if not self._is_running():
            last_speedtest_data = self._get_last_speedtest_data()
            speedtest_data = self._get_speedtest_data()
            cached_until = self.cache_timeout
            if speedtest_data:
                self.py3.storage_set('speedtest_data', speedtest_data)
                if last_speedtest_data:
                    speedtest_data.update(last_speedtest_data)

                # thresholds
                for x in self.thresholds:
                    if x in speedtest_data:
                        self.py3.threshold_get_color(speedtest_data[x], x)

                # units
                for x in ['download', 'upload']:
                    rate, unit = self.py3.format_units(speedtest_data[x], unit='MB/s', si=self.si_units)
                    speedtest_data[x] = str(rate) + ' ' + unit

                for x in ['bytes_received', 'bytes_sent']:
                    size, unit = self.py3.format_units(speedtest_data[x], unit='MB', si=self.si_units)
                    speedtest_data[x] = str(size) + ' ' + unit

        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(self.format, speedtest_data)
        }


    def on_click(self, event):
        pass

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
