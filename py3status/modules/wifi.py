# -*- coding: utf-8 -*-
"""
Display WiFi bit rate, quality, signal and SSID using iw.

Configuration parameters:
    bitrate_bad: Bad bit rate in Mbit/s (default 26)
    bitrate_degraded: Degraded bit rate in Mbit/s (default 53)
    blocks: a string, where each character represents quality level
        (default "_▁▂▃▄▅▆▇█")
    cache_timeout: Update interval in seconds (default 10)
    device: Wireless device name (default "wlan0")
    down_color: Output color when disconnected, possible values:
        "good", "degraded", "bad" (default "bad")
    format_down: Output when disconnected (default "W: down")
    format_up: See placeholders below
        (default "W: {bitrate} {signal_percent} {ssid}")
    round_bitrate: If true, bit rate is rounded to the nearest whole number
        (default True)
    signal_bad: Bad signal strength in percent (default 29)
    signal_degraded: Degraded signal strength in percent (default 49)
    use_sudo: Use sudo to run iw, make sure iw requires no password by
        adding a sudoers entry like
        "<username> ALL=(ALL) NOPASSWD: /usr/bin/iw dev wl* link"
        (default False)

Format placeholders:
    {bitrate} Display bit rate
    {device} Display device name
    {icon} Character representing the quality based on bitrate,
        as defined by the 'blocks'
    {ip} Display IP address
    {signal_dbm} Display signal in dBm
    {signal_percent} Display signal in percent
    {ssid} Display SSID

Color options:
    color_bad: Signal strength signal_bad or lower
    color_degraded: Signal strength signal_degraded or lower
    color_good: Signal strength above signal_degraded

Requires:
    iw:
    ip: if {ip} is used

@author Markus Weimar <mail@markusweimar.de>
@license BSD
"""

import re
import subprocess
import math


class Py3status:
    """
    """
    # available configuration parameters
    bitrate_bad = 26
    bitrate_degraded = 53
    blocks = u"_▁▂▃▄▅▆▇█"
    cache_timeout = 10
    device = 'wlan0'
    down_color = 'bad'
    format_down = 'W: down'
    format_up = 'W: {bitrate} {signal_percent} {ssid}'
    round_bitrate = True
    signal_bad = 29
    signal_degraded = 49
    use_sudo = False

    def __init__(self):
        self._ssid = None
        self._max_bitrate = 0
        # Try and guess the wifi interface
        try:
            cmd = ['iw', 'dev']
            iw = subprocess.check_output(cmd).decode('utf-8')

            devices = re.findall('Interface\s*([^\s]+)', iw)
            if not devices or 'wlan0' in devices:
                self.device = 'wlan0'
            else:
                self.device = devices[0]
        except:
            pass

    def get_wifi(self):
        """
        Get WiFi status using iw.
        """
        self.signal_dbm_bad = self._percent_to_dbm(self.signal_bad)
        self.signal_dbm_degraded = self._percent_to_dbm(self.signal_degraded)

        cmd = ['iw', 'dev', self.device, 'link']
        if self.use_sudo:
            cmd.insert(0, 'sudo')
        iw = subprocess.check_output(cmd).decode('utf-8')

        bitrate_out = re.search('tx bitrate: ([^\s]+) ([^\s]+)', iw)
        if bitrate_out:
            bitrate = float(bitrate_out.group(1))
            if self.round_bitrate:
                bitrate = round(bitrate)
            bitrate_unit = bitrate_out.group(2)
            if bitrate_unit == 'Gbit/s':
                bitrate *= 1000
        else:
            bitrate = None
            bitrate_unit = None
        signal_out = re.search('signal: ([\-0-9]+)', iw)
        if signal_out:
            signal_dbm = int(signal_out.group(1))
            signal_percent = min(self._dbm_to_percent(signal_dbm), 100)
        else:
            signal_dbm = None
            signal_percent = None
        ssid_out = re.search('SSID: (.+)', iw)
        if ssid_out:
            ssid = ssid_out.group(1)
        else:
            ssid = None

        if '{ip}' in self.format_up:
            cmd = ['ip', 'addr', 'list', self.device]
            if self.use_sudo:
                cmd.insert(0, 'sudo')
            ip_info = subprocess.check_output(cmd).decode('utf-8')
            ip_match = re.search('inet\s+([0-9.]+)', ip_info)
            if ip_match:
                ip = ip_match.group(1)
            else:
                ip = None
        else:
            ip = ''

        # reset _max_bitrate if we have changed network
        if self._ssid != ssid:
            self._ssid = ssid
            self._max_bitrate = self.bitrate_degraded
        if bitrate:
            if bitrate > self._max_bitrate:
                self._max_bitrate = bitrate
            quality = int((bitrate / self._max_bitrate) * 100)
        else:
            quality = 0
        icon = self.blocks[int(math.ceil(quality / 100 * (len(self.blocks) - 1
                                                          )))]

        if ssid is None:
            full_text = self.format_down
            color = getattr(self.py3, 'COLOR_{}'.format(self.down_color.upper()))
        else:
            bad = False
            degraded = False
            if bitrate:
                if bitrate <= self.bitrate_bad:
                    bad = True
                elif bitrate <= self.bitrate_degraded:
                    degraded = True
                bitrate = '{} {}'.format(bitrate, bitrate_unit)
            else:
                bitrate = '? MBit/s'
            if signal_dbm:
                if signal_dbm <= self.signal_dbm_bad:
                    bad = True
                elif signal_dbm <= self.signal_dbm_degraded:
                    degraded = True
                signal_dbm = '{} dBm'.format(signal_dbm)
                signal_percent = '{}%'.format(signal_percent)
            else:
                signal_dbm = '? dBm'
                signal_percent = '?%'

            if bad:
                color = self.py3.COLOR_BAD
            elif degraded:
                color = self.py3.COLOR_DEGRADED
            else:
                color = self.py3.COLOR_GOOD

            full_text = self.py3.safe_format(
                self.format_up,
                dict(
                    bitrate=bitrate,
                    signal_dbm=signal_dbm,
                    signal_percent=signal_percent,
                    ip=ip,
                    device=self.device,
                    icon=icon,
                    ssid=ssid,
                ))

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text,
            'color': color
        }
        return response

    def _dbm_to_percent(self, dbm):
        return 2 * (dbm + 100)

    def _percent_to_dbm(self, percent):
        return (percent / 2) - 100


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
