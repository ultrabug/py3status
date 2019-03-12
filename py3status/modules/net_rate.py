# -*- coding: utf-8 -*-
"""
Display network transfer rate.

Configuration parameters:
    all_interfaces: ignore self.interfaces, but not self.interfaces_blacklist
        (default True)
    cache_timeout: how often we refresh this module in seconds
        (default 2)
    devfile: location of dev file under /proc
        (default '/proc/net/dev')
    format: format of the module output
        (default '{interface}: {total}')
    format_no_connection: when there is no data transmitted from the start of the plugin
        (default '')
    format_value: format to use for values
        (default "[\?min_length=11 {value:.1f} {unit}]")
    hide_if_zero: hide indicator if rate == 0
        (default False)
    interfaces: comma separated list of interfaces to track
        (default [])
    interfaces_blacklist: comma separated list of interfaces to ignore
        (default 'lo')
    si_units: use SI units
        (default False)
    sum_values: sum values of each interface instead of taking the top one
        (default False)
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')])
    unit: unit to use. If the unit contains a multiplier prefix, only this
        exact unit will ever be used
        (default "B/s")

Format placeholders:
    {down} download rate
    {interface} name of interface
    {total} total rate
    {up} upload rate

format_value placeholders:
    {unit} current unit
    {value} numeric value

Color thresholds:
    {down} Change color based on the value of down
    {total} Change color based on the value of total
    {up} Change color based on the value of up

@author shadowprince
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': 'eno1:  852.2 KiB/s'}
"""

from __future__ import division  # python2 compatibility
from time import time


class Py3status:
    """
    """

    # available configuration parameters
    all_interfaces = True
    cache_timeout = 2
    devfile = "/proc/net/dev"
    format = "{interface}: {total}"
    format_no_connection = ""
    format_value = "[\?min_length=11 {value:.1f} {unit}]"
    hide_if_zero = False
    interfaces = []
    interfaces_blacklist = "lo"
    si_units = False
    sum_values = False
    thresholds = [(0, "bad"), (1024, "degraded"), (1024 * 1024, "good")]
    unit = "B/s"

    class Meta:
        def deprecate_function(config):
            # support old thresholds
            precision = config.get("precision", 1)
            padding = 3 + 1 + precision + 1 + 5
            format_value = "[\?min_length={padding} {{value:.{precision}f}} {{unit}}]".format(
                padding=padding, precision=precision
            )
            return {"format_value": format_value}

        deprecated = {
            "function": [{"function": deprecate_function}],
            "remove": [
                {"param": "precision", "msg": "obsolete, use format_value instead"}
            ],
        }

    def post_config_hook(self):
        # parse some configuration parameters
        if not isinstance(self.interfaces, list):
            self.interfaces = self.interfaces.split(",")
        if not isinstance(self.interfaces_blacklist, list):
            self.interfaces_blacklist = self.interfaces_blacklist.split(",")
        placeholders = self.py3.get_placeholder_formats_list(self.format_value)
        values = ["{%s}" % x[1] for x in placeholders if x[0] == "value"]
        self._value_formats = values
        # last
        self.last_interface = None
        self.last_stat = self._get_stat()
        self.last_time = time()

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def net_rate(self):
        ns = self._get_stat()
        deltas = {}
        try:
            # time from previous check
            timedelta = time() - self.last_time

            # calculate deltas for all interfaces
            for old, new in zip(self.last_stat, ns):
                down = int(new[1]) - int(old[1])
                up = int(new[9]) - int(old[9])

                down /= timedelta
                up /= timedelta

                deltas[new[0]] = {"total": up + down, "up": up, "down": down}

            # update last_ info
            self.last_stat = self._get_stat()
            self.last_time = time()

            # get the interface with max rate
            if self.sum_values:
                interface = "sum"
                sum_up = sum([itm["up"] for _, itm in deltas.items()])
                sum_down = sum([itm["down"] for _, itm in deltas.items()])
                deltas[interface] = {
                    "total": sum_up + sum_down,
                    "up": sum_up,
                    "down": sum_down,
                }
            else:
                interface = max(deltas, key=lambda x: deltas[x]["total"])

            # if there is no rate - show last active interface, or hide

            # we need to check if it will be zero after it is formatted
            # with the desired unit eg MB/s
            total, _ = self.py3.format_units(
                deltas[interface]["total"], unit=self.unit, si=self.si_units
            )
            values = [float(x.format(total)) for x in self._value_formats]
            if max(values) == 0:
                interface = self.last_interface
                hide = self.hide_if_zero
            # if there is - update last_interface
            else:
                self.last_interface = interface
                hide = False

            # get the deltas into variable
            delta = deltas[interface] if interface else None

        except (TypeError, ValueError, KeyError):
            delta = None
            interface = None
            hide = self.hide_if_zero

        response = {"cached_until": self.py3.time_in(self.cache_timeout)}

        if hide:
            response["full_text"] = ""
        elif not interface:
            response["full_text"] = self.format_no_connection
        else:
            for x in self.thresholds_init:
                if x in delta:
                    self.py3.threshold_get_color(delta[x], x)

            response["full_text"] = self.py3.safe_format(
                self.format,
                {
                    "down": self._format_value(delta["down"]),
                    "total": self._format_value(delta["total"]),
                    "up": self._format_value(delta["up"]),
                    "interface": interface[:-1],
                },
            )

        return response

    def _get_stat(self):
        """
        Get statistics from devfile in list of lists of words
        """

        def dev_filter(x):
            # get first word and remove trailing interface number
            x = x.strip().split(" ")[0][:-1]

            if x in self.interfaces_blacklist:
                return False

            if self.all_interfaces:
                return True

            if x in self.interfaces:
                return True

            return False

        # read devfile, skip two header files
        x = filter(dev_filter, open(self.devfile).readlines()[2:])

        try:
            # split info into words, filter empty ones
            return [list(filter(lambda x: x, _x.split(" "))) for _x in x]

        except StopIteration:
            return None

    def _format_value(self, value):
        """
        Return formatted string
        """
        value, unit = self.py3.format_units(value, unit=self.unit, si=self.si_units)
        return self.py3.safe_format(self.format_value, {"value": value, "unit": unit})


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
