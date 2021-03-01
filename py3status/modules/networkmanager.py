r"""
Display NetworkManager fields via nmcli, a command-line tool.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    devices: specify a list of devices to use (default ['[e|w]*'])
    format: display format for this module (default '{format_device}')
    format_device: format for devices
        *(default "[\?if=general_connection {general_device}[\?soft  ][\?color=ap_signal {ap_ssid} {ap_bars} {ap_signal}%][\?soft  ][\?color=good {ip4_address1}]]")*
    format_device_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (30, 'degraded'), (65, 'good')])

Format placeholders:
    {format_device} format for devices

Format_device placeholders:
    {general_connection} eg Py3status, Wired Connection 1
    {general_device}     eg wlp3s0b1, enp2s0
    {general_type}       eg wifi, ethernet
    {ap_bars}            signal strength in bars, eg ▂▄▆_
    {ap_chan}            wifi channel, eg 6
    {ap_mode}            network mode, eg Adhoc or Infra
    {ap_rate}            bitrate, eg 54 Mbit/s
    {ap_security}        signal security, eg WPA2
    {ap_signal}          signal strength in percentage, eg 63
    {ap_ssid}            ssid name, eg Py3status
    {ip4_address1}       eg 192.168.1.108
    {ip6_address1}       eg 0000::0000:0000:0000:0000

    Use `nmcli --terse --fields=general,ap,ip4,ip6 device show` for a full list of
    supported NetworkManager fields to use. Not all of NetworkManager fields will
    be usable. See `man nmcli` for more information.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    nmcli: cli configuration utility for NetworkManager

Examples:
```
# specify devices to use
networkmanager {
    devices = ['e*']    # ethernet only
    devices = ['w*']    # wireless only
    devices = []        # ethernet, wireless, lo, etc
}
```

@author Kevin Pulo <kev@pulo.com.au>
@license BSD

SAMPLE OUTPUT
[{'full_text': 'enp2s0 '}, {'color': '#00FF00', 'full_text': '192.168.1.108'}]

wifi
[
    {'full_text': 'wlp3s0b1 '},
    {'color': '#FFFF00', 'full_text': 'Py3net ▂▄__ 54% '},
    {'color': '#00FF00', 'full_text': '192.168.1.106'},
]
"""

from fnmatch import fnmatch

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    devices = ["[e|w]*"]
    format = "{format_device}"
    format_device = (
        r"[\?if=general_connection {general_device}[\?soft  ]"
        r"[\?color=ap_signal {ap_ssid} {ap_bars} {ap_signal}%][\?soft  ]"
        r"[\?color=good {ip4_address1}]]"
    )
    format_device_separator = " "
    thresholds = [(0, "bad"), (30, "degraded"), (65, "good")]

    def post_config_hook(self):
        command = "nmcli --terse --colors=no"
        if not self.py3.check_commands(command.split()[0]):
            raise Exception(STRING_NOT_INSTALLED)

        self.first_run = True

        addresses = [
            x.split("_")[0]
            for x in self.py3.get_placeholders_list(
                self.format_device, "ip[46]_address[0123456789]"
            )
        ]

        self.nmcli_command = "{} --fields={} device show".format(
            command, ",".join(["general", "ap"] + addresses)
        ).split()
        self.caches = {"lines": {}, "devices": {}}
        self.devices = {"list": [], "devices": self.devices}
        self.thresholds_init = self.py3.get_color_names_list(self.format_device)

    def _update_key(self, key):
        for old, new in [("[", ""), ("]", ""), (".", "_"), ("-", "_")]:
            key = key.replace(old, new)
        return key.lower()

    def networkmanager(self):
        nm_data = self.py3.command_output(self.nmcli_command, localized=True)
        new_device = []
        used_ap = None

        for chunk in nm_data.split("\n\n"):
            lines = chunk.splitlines()
            key, value = lines[0].split(":", 1)
            if self.first_run:
                if self.devices["devices"]:
                    for _filter in self.devices["devices"]:
                        if fnmatch(value, _filter):
                            self.devices["list"].append(value)
            if value not in self.devices["list"]:
                continue

            try:
                key = self.caches["devices"][key]
            except KeyError:
                new_key = self._update_key(key)

                self.caches["devices"][key] = new_key
                key = self.caches["devices"][key]

            device = {key: value}
            for line in lines[1:]:
                try:
                    key, value = self.caches["lines"][line]
                except (KeyError, ValueError):
                    key, value = line.split(":", 1)
                    key = self._update_key(key)
                    if "IP" in line and "ADDRESS" in line:
                        value = value.split("/")[0]
                    else:
                        try:
                            value = int(value)
                        except ValueError:
                            pass

                    self.caches["lines"][line] = (key, value)

                if "ap" in key and "in_use" in key and value == "*":
                    used_ap = key.split("_")[0]
                device[key] = value

            # Add specific extra entries for the AP currently used by the device.
            if used_ap is not None:
                current_ap = {}
                for key in device:
                    if key.startswith(used_ap + "_"):
                        current_ap[key.replace(used_ap + "_", "ap_")] = device[key]
                device.update(current_ap)

            for x in self.thresholds_init:
                if x in device:
                    self.py3.threshold_get_color(device[x], x)

            new_device.append(self.py3.safe_format(self.format_device, device))

        format_device_separator = self.py3.safe_format(self.format_device_separator)
        format_device = self.py3.composite_join(format_device_separator, new_device)

        self.first_run = False

        return {
            "cache_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format, {"format_device": format_device}
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
