# -*- coding: utf-8 -*-
"""
Display WiFi info using NetworkManager.

Configuration parameters:
    cache_timeout: Update interval in seconds (default 5)
    device: Wireless device name (default "wlan0" or first wifi device)
    down_color: Output color when disconnected, possible values:
        "good", "degraded", "bad" (default "bad")
    format: Display format for this module
        (default '{bars} {signal}% {ssid}|down')
    thresholds: Color thresholds for signal value.
        (default [(0, 'bad'), (30, 'degraded'), (55, 'good')])

Format placeholders:
    {bars} Graphical signal strength
    {chan} Channel
    {device} Device name
    {mode} Mode ("Infra" or "Adhoc")
    {rate} Bit rate
    {security} Security protocols supported
    {signal} Signal strength
    {ssid} SSID

    Maybe more, check `nmcli -f ap d show` on your system.

Color options:
    color_bad: Signal strength 30 or lower (1 bar)
    color_degraded: Signal strength 31 -- 54 (2 bars)
    color_good: Signal strength above 55 (3 or 4 bars)

Requires:
    nmcli: cli configuration utility for NetworkManager

@author Kevin Pulo <kev@pulo.com.au>
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u2582\u2584\u2586\u2588 91% Chicken Remixed'}
"""

STRING_ERROR = "nmcli: command failed"
DEFAULT_FORMAT = "{bars} {signal}% {ssid}|down"

class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    device = None
    down_color = "bad"
    format = DEFAULT_FORMAT
    thresholds = [(0, "bad"), (30, "degraded"), (55, "good")]

    def post_config_hook(self):
        self.nmcli_cmd = self.py3.check_commands(["nmcli", "/usr/bin/nmcli"])
        if not self.device:
            # Try to guess the wifi interface
            cmd = [self.nmcli_cmd, "--terse", "-mode", "tabular", "--colors", "no", "--fields", "device,type", "device", "status"]
            try:
                output = self.py3.command_output(cmd)
                devices = []
                for line in output.splitlines():
                    (device, _type) = line.split(":", 1)
                    if _type == "wifi":
                        devices.append(device)
                if not devices or "wlan0" in devices:
                    self.device = "wlan0"
                else:
                    self.device = devices[0]
            except:
                pass

    def wifi(self):
        """
        Get WiFi status using NetworkManager.
        """
        cmd = [self.nmcli_cmd, "--terse", "--mode", "multiline", "--colors", "no", "--fields", "ap", "device", "show", self.device]
        try:
            output = self.py3.command_output(cmd, localized=True)
            if not output or not isinstance(output, basestring):
                raise Exception()
        except:
            return {"cache_until": self.py3.time_in(self.cache_timeout),
                    "color": self.py3.COLOR_ERROR or self.py3.COLOR_BAD,
                    "full_text": STRING_ERROR}

        data = { }
        connected_ap = None
        for line in output.splitlines():
            (key, value) = line.split(":", 1)
            (ap, field) = key.split(".", 1)
            if field == "*" and value == "*":
                connected_ap = ap
            elif field == "IN-USE" and value == "*":
                connected_ap = ap
            elif ap == connected_ap:
                data[field.lower()] = value

        # special case fix some of the chars used by bars.
        # in proportional fonts, underscore can have a different width than lower-eighth-block
        if "bars" not in data or not isinstance(data["bars"], basestring):
            data["bars"] = ""
        data["bars"] = data["bars"].replace(u"_", u"▁")

        color = self.py3.COLOR_GOOD
        if connected_ap is None:
            # wifi down
            color = getattr(self.py3, "COLOR_{}".format(self.down_color.upper()))
            full_text = self.py3.safe_format(self.format)
        else:
            # wifi up
            try:
                color = self.py3.threshold_get_color(int(data["signal"]))
            except:
                pass
            full_text = self.py3.safe_format(self.format, data)

        return {
            "cache_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
            "color": color,
        }

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
