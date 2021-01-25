"""
Display WiFi bit rate, quality, signal and SSID using iw.

Configuration parameters:
    bitrate_bad: Bad bit rate in Mbit/s (default 26)
    bitrate_degraded: Degraded bit rate in Mbit/s (default 53)
    blocks: a string, where each character represents quality level
        (default "_▁▂▃▄▅▆▇█")
    cache_timeout: Update interval in seconds (default 10)
    device: specify name or MAC address of device to use, otherwise auto
        (default None)
    down_color: Output color when disconnected, possible values:
        "good", "degraded", "bad" (default "bad")
    format: Display format for this module
        (default 'W: {bitrate} {bitrate_unit} {signal_percent}% {ssid}|W: down')
    signal_bad: Bad signal strength in percent (default 29)
    signal_degraded: Degraded signal strength in percent (default 49)
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {bitrate} Display bitrate
    {bitrate_unit} Display bitrate unit
    {device} Display device name
    {freq_ghz} Network frequency in Ghz
    {freq_mhz} Network frequency in Mhz
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

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    iw: cli configuration utility for wireless devices
    ip: only for {ip}. may be part of iproute2: ip routing utilities

Notes:
    Some distributions require commands to be run with privileges. You can
    give commands some root rights to run without a password by editing
    sudoers file, i.e., `sudo visudo`, and add a line that requires sudo.
    '<user> ALL=(ALL) NOPASSWD:/sbin/iw dev,/sbin/iw dev [a-z]* link'
    '<user> ALL=(ALL) NOPASSWD:/sbin/ip addr list [a-z]*'

@author Markus Weimar <mail@markusweimar.de>
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'W: 54.0 MBit/s 100% Chicken Remixed'}
"""

import re
import math

DEFAULT_FORMAT = "W: {bitrate} {bitrate_unit} {signal_percent}% {ssid}|W: down"
STRING_NOT_INSTALLED = "iw not installed"
STRING_NO_DEVICE = "no available device"


class Py3status:
    """
    """

    # available configuration parameters
    bitrate_bad = 26
    bitrate_degraded = 53
    blocks = "_▁▂▃▄▅▆▇█"
    cache_timeout = 10
    device = None
    down_color = "bad"
    format = DEFAULT_FORMAT
    signal_bad = 29
    signal_degraded = 49
    thresholds = []

    class Meta:
        deprecated = {
            "remove": [
                {"param": "use_sudo", "msg": "obsolete"},
                {"param": "round_bitrate", "msg": "obsolete"},
            ]
        }
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {"signal_percent": ":g", "bitrate": ":g"},
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        iw = self.py3.check_commands(["iw", "/sbin/iw"])
        if not iw:
            raise Exception(STRING_NOT_INSTALLED)

        # get wireless interface
        try:
            data = self.py3.command_output([iw, "dev"])
        except self.py3.CommandError as ce:
            raise Exception(ce.error.strip())
        last_device = None
        for line in data.splitlines()[1:]:
            if not line.startswith("\t\t"):
                last_device = None
            if "Interface" in line or ("addr" in line and last_device is not None):
                intf_or_addr = line.split()[-1]
                if "Interface" in line:
                    last_device = intf_or_addr
                if not self.device or intf_or_addr.lower() == self.device.lower():
                    self.device = last_device
                    break
        else:
            device = f" `{self.device}`" if self.device else ""
            raise Exception(STRING_NO_DEVICE + device)

        self._max_bitrate = 0
        self._ssid = ""
        self.color_down = getattr(self.py3, f"COLOR_{self.down_color.upper()}")
        self.commands = set()
        self.ip_addr_list_id = ["ip", "addr", "list", self.device]
        self.iw_dev_id_link = [iw, "dev", self.device, "link"]
        self.signal_dbm_bad = self._percent_to_dbm(self.signal_bad)
        self.signal_dbm_degraded = self._percent_to_dbm(self.signal_degraded)
        self.thresholds_init = self.py3.get_color_names_list(self.format)

        # DEPRECATION WARNING
        format_down = getattr(self, "format_down", None)
        format_up = getattr(self, "format_up", None)

        if self.format != DEFAULT_FORMAT:
            return

        if format_up or format_down:
            self.format = "{}|{}".format(
                format_up or "W: {bitrate} {bitrate_unit} {signal_percent}% {ssid}",
                format_down or "W: down",
            )
            msg = "DEPRECATION WARNING: you are using old style configuration "
            msg += "parameters you should update to use the new format."
            self.py3.log(msg)

    def _dbm_to_percent(self, dbm):
        return 2 * (dbm + 100)

    def _percent_to_dbm(self, percent):
        return (percent / 2) - 100

    def _get_wifi_data(self, command):
        for _ in range(2):
            try:
                return self.py3.command_output(command)
            except self.py3.CommandError as ce:
                if str(command) not in self.commands:
                    command[0:0] = ["sudo", "-n"]
                    continue
                msg = ce.error.strip().replace("sudo", " ".join(command[2:]))
                self.py3.error(msg, self.py3.CACHE_FOREVER)
            finally:
                self.commands.add(str(command))

    def wifi(self):
        iw = self._get_wifi_data(self.iw_dev_id_link)

        bitrate = None
        bitrate_unit = None
        freq_ghz = None
        freq_mhz = None
        icon = None
        ip = None
        signal_dbm = None
        signal_percent = None
        ssid = None
        color = self.color_down
        quality = 0

        # bitrate
        bitrate_out = re.search(r"tx bitrate: ([^\s]+) ([^\s]+)", iw)
        if bitrate_out:
            bitrate = float(bitrate_out.group(1))
            bitrate_unit = bitrate_out.group(2)
            if bitrate_unit == "Gbit/s":
                bitrate *= 1000

        # signal
        signal_out = re.search(r"signal: ([\-0-9]+)", iw)
        if signal_out:
            signal_dbm = int(signal_out.group(1))
            signal_percent = min(self._dbm_to_percent(signal_dbm), 100)

        # ssid
        ssid_out = re.search(r"SSID: (.+)", iw)
        if ssid_out:
            ssid = ssid_out.group(1)
            # `iw` command would prints unicode SSID like `\xe8\x8b\x9f`
            # the `ssid` here would be '\\xe8\\x8b\\x9f' (note the escape)
            # it needs to be decoded using 'unicode_escape', to '苟'
            ssid = ssid.encode("latin-1").decode("unicode_escape")
            ssid = ssid.encode("latin-1").decode("utf-8")

        # frequency
        freq_out = re.search(r"freq: ([\-0-9]+)", iw)
        if freq_out:
            freq_mhz = int(freq_out.group(1))
            freq_ghz = freq_mhz / 1000

        # ip
        if self.py3.format_contains(self.format, "ip"):
            ip_info = self._get_wifi_data(self.ip_addr_list_id)
            ip_match = re.search(r"inet\s+([0-9.]+)", ip_info)
            if ip_match:
                ip = ip_match.group(1)

        # reset _max_bitrate if we have changed network
        if self._ssid != ssid:
            self._ssid = ssid
            self._max_bitrate = self.bitrate_degraded
        if bitrate:
            if bitrate > self._max_bitrate:
                self._max_bitrate = bitrate
            quality = int((bitrate / self._max_bitrate) * 100)

        # wifi
        if ssid is not None:
            icon = self.blocks[math.ceil(quality / 100 * (len(self.blocks) - 1))]
            color = self.py3.COLOR_GOOD
            if bitrate:
                if bitrate <= self.bitrate_bad:
                    color = self.py3.COLOR_BAD
                elif bitrate <= self.bitrate_degraded:
                    color = self.py3.COLOR_DEGRADED
            if signal_dbm:
                if signal_dbm <= self.signal_dbm_bad:
                    color = self.py3.COLOR_BAD
                elif signal_dbm <= self.signal_dbm_degraded:
                    color = self.py3.COLOR_DEGRADED

        wifi_data = {
            "bitrate": bitrate,
            "bitrate_unit": bitrate_unit,
            "device": self.device,
            "freq_ghz": freq_ghz,
            "freq_mhz": freq_mhz,
            "icon": icon,
            "ip": ip,
            "signal_dbm": signal_dbm,
            "signal_percent": signal_percent,
            "ssid": ssid,
        }

        for x in self.thresholds_init:
            if x in wifi_data:
                self.py3.threshold_get_color(wifi_data[x], x)

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, wifi_data),
        }
        if not self.thresholds_init:
            response["color"] = color
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
