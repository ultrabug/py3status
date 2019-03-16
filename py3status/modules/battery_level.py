# -*- coding: utf-8 -*-
"""
Display battery information.

Configuration parameters:
    battery_id: id of the battery to be displayed
        set to 'all' for combined display of all batteries
        (default 0)
    blocks: a string, where each character represents battery level
        especially useful when using icon fonts (e.g. FontAwesome)
        (default "_▁▂▃▄▅▆▇█")
    cache_timeout: a timeout to refresh the battery state
        (default 60)
    charging_character: a character to represent charging battery
        especially useful when using icon fonts (e.g. FontAwesome)
        (default "⚡")
    format: string that formats the output. See placeholders below.
        (default "{icon}")
    format_notify_charging: format of the notification received when you click
        on the module while your computer is plugged in
        (default 'Charging ({percent}%)')
    format_notify_discharging: format of the notification received when you
        click on the module while your computer is not plugged in
        (default "{time_remaining}")
    hide_seconds: hide seconds in remaining time
        (default False)
    hide_when_full: hide any information when battery is fully charged (when
        the battery level is greater than or equal to 'threshold_full')
        (default False)
    measurement_mode: either 'acpi' or 'sys', or None to autodetect. 'sys'
        should be more robust and does not have any extra requirements, however
        the time measurement may not work in some cases
        (default None)
    notification: show current battery state as notification on click
        (default False)
    notify_low_level: display notification when battery is running low (when
        the battery level is less than 'threshold_degraded')
        (default False)
    on_udev_power_supply: dynamic variable to watch for `power_supply` udev subsystem
        events to trigger specified action.
        (default "refresh")
    sys_battery_path: set the path to your battery(ies), without including its
        number
        (default "/sys/class/power_supply/")
    threshold_bad: a percentage below which the battery level should be
        considered bad
        (default 10)
    threshold_degraded: a percentage below which the battery level should be
        considered degraded
        (default 30)
    threshold_full: a percentage at or above which the battery level should
        should be considered full
        (default 100)

Format placeholders:
    {ascii_bar} - a string of ascii characters representing the battery level,
        an alternative visualization to '{icon}' option
    {icon} - a character representing the battery level,
        as defined by the 'blocks' and 'charging_character' parameters
    {percent} - the remaining battery percentage (previously '{}')
    {time_remaining} - the remaining time until the battery is empty

Color options:
    color_bad: Battery level is below threshold_bad
    color_charging: Battery is charging (default "#FCE94F")
    color_degraded: Battery level is below threshold_degraded
    color_good: Battery level is above thresholds

Requires:
    - the `acpi` the acpi command line utility (only if
        `measurement_mode='acpi'`)

@author shadowprince, AdamBSteele, maximbaz, 4iar, m45t3r
@license Eclipse Public License

SAMPLE OUTPUT
{'color': '#FCE94F', 'full_text': u'\u26a1'}

discharging
{'color': '#FF0000', 'full_text': u'\u2340'}
"""

from __future__ import division  # python2 compatibility
from re import findall
from glob import iglob

import math
import os

BLOCKS = u"_▁▂▃▄▅▆▇█"
CHARGING_CHARACTER = u"⚡"
EMPTY_BLOCK_CHARGING = u"|"
EMPTY_BLOCK_DISCHARGING = u"⍀"
FULL_BLOCK = u"█"
FORMAT = u"{icon}"
FORMAT_NOTIFY_CHARGING = u"Charging ({percent}%)"
FORMAT_NOTIFY_DISCHARGING = u"{time_remaining}"
SYS_BATTERY_PATH = u"/sys/class/power_supply/"
MEASUREMENT_MODE = None
FULLY_CHARGED = u"?"


class Py3status:
    """
    """

    # available configuration parameters
    battery_id = 0
    blocks = BLOCKS
    cache_timeout = 60
    charging_character = CHARGING_CHARACTER
    format = FORMAT
    format_notify_charging = FORMAT_NOTIFY_CHARGING
    format_notify_discharging = FORMAT_NOTIFY_DISCHARGING
    hide_seconds = False
    hide_when_full = False
    measurement_mode = MEASUREMENT_MODE
    notification = False
    notify_low_level = False
    on_udev_power_supply = "refresh"
    sys_battery_path = SYS_BATTERY_PATH
    threshold_bad = 10
    threshold_degraded = 30
    threshold_full = 100

    class Meta:
        deprecated = {
            "format_fix_unnamed_param": [
                {
                    "param": "format",
                    "placeholder": "percent",
                    "msg": "{} should not be used in format use `{percent}`",
                }
            ],
            "substitute_by_value": [
                {
                    "param": "mode",
                    "value": "ascii_bar",
                    "substitute": {"param": "format", "value": "{ascii_bar}"},
                    "msg": 'obsolete parameter use `format = "{ascii_bar}"`',
                },
                {
                    "param": "mode",
                    "value": "text",
                    "substitute": {"param": "format", "value": "Battery: {percent}"},
                    "msg": 'obsolete parameter use `format = "{percent}"`',
                },
                {
                    "param": "show_percent_with_blocks",
                    "value": True,
                    "substitute": {"param": "format", "value": "{icon} {percent}%"},
                    "msg": 'obsolete parameter use `format = "{icon} {percent}%"`',
                },
            ],
        }

    def post_config_hook(self):
        self.last_known_status = ""
        # Guess mode if not set
        if self.measurement_mode is None:
            if os.path.isdir(self.sys_battery_path):
                self.measurement_mode = "sys"
            elif self.py3.check_commands(["acpi"]):
                self.measurement_mode = "acpi"

        msg = "measurement_mode `{}`".format(self.measurement_mode)
        if self.measurement_mode == "sys":
            self.get_battery_info = self._extract_battery_info_from_sys
        elif self.measurement_mode == "acpi":
            self.get_battery_info = self._extract_battery_info_from_acpi
        else:
            raise NameError("invalid {}".format(msg))
        self.py3.log("selected {}".format(msg))

    def battery_level(self):
        battery_list = self.get_battery_info()
        if not battery_list:
            return {
                "full_text": "",
                "cached_until": self.py3.time_in(self.cache_timeout),
            }

        self._refresh_battery_info(battery_list)
        self._update_icon()
        self._update_ascii_bar()
        self._update_full_text()

        return self._build_response()

    def on_click(self, event):
        """
        Display a notification following the specified format
        """
        if not self.notification:
            return

        if self.charging:
            format = self.format_notify_charging
        else:
            format = self.format_notify_discharging

        message = self.py3.safe_format(
            format,
            dict(
                ascii_bar=self.ascii_bar,
                icon=self.icon,
                percent=self.percent_charged,
                time_remaining=self.time_remaining,
            ),
        )

        if message:
            self.py3.notify_user(message, "info")

    def _extract_battery_info_from_acpi(self):
        """
        Get the battery info from acpi

        # Example acpi -bi raw output (Discharging):
        Battery 0: Discharging, 94%, 09:23:28 remaining
        Battery 0: design capacity 5703 mAh, last full capacity 5283 mAh = 92%
        Battery 1: Unknown, 98%
        Battery 1: design capacity 1880 mAh, last full capacity 1370 mAh = 72%

        # Example Charging
        Battery 0: Charging, 96%, 00:20:40 until charged
        Battery 0: design capacity 5566 mAh, last full capacity 5156 mAh = 92%
        Battery 1: Unknown, 98%
        Battery 1: design capacity 1879 mAh, last full capacity 1370 mAh = 72%
        """

        def _parse_battery_info(acpi_battery_lines):
            battery = {}
            battery["percent_charged"] = int(
                findall("(?<= )(\d+)(?=%)", acpi_battery_lines[0])[0]
            )
            battery["charging"] = "Charging" in acpi_battery_lines[0]
            battery["capacity"] = int(
                findall("(?<= )(\d+)(?= mAh)", acpi_battery_lines[1])[1]
            )

            # ACPI only shows time remaining if battery is discharging or
            # charging
            try:
                battery["time_remaining"] = "".join(
                    findall(
                        "(?<=, )(\d+:\d+:\d+)(?= remaining)|"
                        "(?<=, )(\d+:\d+:\d+)(?= until)",
                        acpi_battery_lines[0],
                    )[0]
                )
            except IndexError:
                battery["time_remaining"] = FULLY_CHARGED

            return battery

        acpi_list = self.py3.command_output(["acpi", "-b", "-i"]).splitlines()

        # Separate the output because each pair of lines corresponds to a
        # single battery.  Now the list index will correspond to the index of
        # the battery we want to look at
        acpi_list = [acpi_list[i : i + 2] for i in range(0, len(acpi_list) - 1, 2)]

        return [_parse_battery_info(battery) for battery in acpi_list]

    def _extract_battery_info_from_sys(self):
        """
        Extract the percent charged, charging state, time remaining,
        and capacity for a battery, using Linux's kernel /sys interface

        Only available in kernel 2.6.24(?) and newer. Before kernel provided
        a similar, yet incompatible interface in /proc
        """

        if not os.listdir(self.sys_battery_path):
            return []

        def _parse_battery_info(sys_path):
            """
            Extract battery information from uevent file, already convert to
            int if necessary
            """
            raw_values = {}
            with open(os.path.join(sys_path, u"uevent")) as f:
                for var in f.read().splitlines():
                    k, v = var.split("=")
                    try:
                        raw_values[k] = int(v)
                    except ValueError:
                        raw_values[k] = v
            return raw_values

        battery_list = []
        for path in iglob(os.path.join(self.sys_battery_path, "BAT*")):
            r = _parse_battery_info(path)

            capacity = r.get(
                "POWER_SUPPLY_ENERGY_FULL", r.get("POWER_SUPPLY_CHARGE_FULL")
            )
            present_rate = r.get(
                "POWER_SUPPLY_POWER_NOW",
                r.get("POWER_SUPPLY_CURRENT_NOW", r.get("POWER_SUPPLY_VOLTAGE_NOW")),
            )
            remaining_energy = r.get(
                "POWER_SUPPLY_ENERGY_NOW", r.get("POWER_SUPPLY_CHARGE_NOW")
            )

            battery = {}
            battery["capacity"] = capacity
            battery["charging"] = "Charging" in r["POWER_SUPPLY_STATUS"]
            battery["percent_charged"] = int(
                math.floor(remaining_energy / capacity * 100)
            )
            try:
                if battery["charging"]:
                    time_in_secs = (capacity - remaining_energy) / present_rate * 3600
                else:
                    time_in_secs = remaining_energy / present_rate * 3600
                battery["time_remaining"] = self._seconds_to_hms(time_in_secs)
            except ZeroDivisionError:
                # Battery is either full charged or is not discharging
                battery["time_remaining"] = FULLY_CHARGED

            battery_list.append(battery)
        return battery_list

    def _hms_to_seconds(self, t):
        h, m, s = [int(i) for i in t.split(":")]
        return 3600 * h + 60 * m + s

    def _seconds_to_hms(self, secs):
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    def _refresh_battery_info(self, battery_list):
        if type(self.battery_id) == int:
            battery = battery_list[self.battery_id]
            self.percent_charged = battery["percent_charged"]
            self.charging = battery["charging"]
            self.time_remaining = battery["time_remaining"]

        elif self.battery_id == "all":
            total_capacity = sum([battery["capacity"] for battery in battery_list])

            # Average and weigh % charged by the capacities of the batteries so
            # that self.percent_charged properly represents batteries that have
            # different capacities.
            self.percent_charged = int(
                sum(
                    [
                        battery["capacity"]
                        / total_capacity
                        * battery["percent_charged"]
                        for battery in battery_list
                    ]
                )
            )

            self.charging = any([battery["charging"] for battery in battery_list])

            # Assumes a system has at max two batteries
            active_battery = None
            inactive_battery = battery_list[:]
            for battery_id in range(0, len(battery_list)):
                if (
                    battery_list[battery_id]["time_remaining"]
                    and battery_list[battery_id]["time_remaining"] != FULLY_CHARGED
                ):
                    active_battery = battery_list[battery_id]
                    del inactive_battery[battery_id]

            # Only one battery will be discharging or charging at a time.
            # Therefore, ACPI does not provide a time remaining value for the
            # other battery.  So the time remaining for the other battery is
            # calculated using the time remaining of the first battery and the
            # capacity values for both batteries.
            if active_battery and inactive_battery:
                inactive_battery = inactive_battery[0]

                time_remaining_seconds = self._hms_to_seconds(
                    active_battery["time_remaining"]
                )
                try:
                    rate_second_per_mah = time_remaining_seconds / (
                        active_battery["capacity"]
                        * (active_battery["percent_charged"] / 100)
                    )
                    time_remaining_seconds += (
                        inactive_battery["capacity"]
                        * inactive_battery["percent_charged"]
                        / 100
                        * rate_second_per_mah
                    )
                except ZeroDivisionError:
                    # Either active or inactive battery has 0% charge
                    time_remaining_seconds = 0
                    rate_second_per_mah = 0

                self.time_remaining = self._seconds_to_hms(time_remaining_seconds)

            elif active_battery:
                self.time_remaining = active_battery["time_remaining"]

            else:
                self.time_remaining = None

        if self.time_remaining and self.hide_seconds:
            self.time_remaining = self.time_remaining[:-3]

    def _update_ascii_bar(self):
        self.ascii_bar = FULL_BLOCK * int(self.percent_charged / 10)
        if self.charging:
            self.ascii_bar += EMPTY_BLOCK_CHARGING * (
                10 - int(self.percent_charged / 10)
            )
        else:
            self.ascii_bar += EMPTY_BLOCK_DISCHARGING * (
                10 - int(self.percent_charged / 10)
            )

    def _update_icon(self):
        if self.charging:
            self.icon = self.charging_character
        else:
            self.icon = self.blocks[
                min(
                    len(self.blocks) - 1,
                    int(math.ceil(self.percent_charged / 100 * (len(self.blocks) - 1))),
                )
            ]

    def _update_full_text(self):
        self.full_text = self.py3.safe_format(
            self.format,
            dict(
                ascii_bar=self.ascii_bar,
                icon=self.icon,
                percent=self.percent_charged,
                time_remaining=self.time_remaining,
            ),
        )

    def _build_response(self):
        self.response = {}

        self._set_bar_text()
        self._set_bar_color()
        self._set_cache_timeout()

        return self.response

    def _set_bar_text(self):
        self.response["full_text"] = (
            ""
            if self.hide_when_full and self.percent_charged >= self.threshold_full
            else self.full_text
        )

    def _set_bar_color(self):
        notify_msg = None
        if self.charging:
            self.response["color"] = self.py3.COLOR_CHARGING or "#FCE94F"
            battery_status = "charging"
        elif self.percent_charged < self.threshold_bad:
            self.response["color"] = self.py3.COLOR_BAD
            battery_status = "bad"
            notify_msg = {
                "msg": "Battery level is critically low ({}%)",
                "level": "error",
            }
        elif self.percent_charged < self.threshold_degraded:
            self.response["color"] = self.py3.COLOR_DEGRADED
            battery_status = "degraded"
            notify_msg = {
                "msg": "Battery level is running low ({}%)",
                "level": "warning",
            }
        elif self.percent_charged >= self.threshold_full:
            self.response["color"] = self.py3.COLOR_GOOD
            battery_status = "full"
        else:
            battery_status = "good"

        if (
            notify_msg
            and self.notify_low_level
            and self.last_known_status != battery_status
        ):
            self.py3.notify_user(
                notify_msg["msg"].format(self.percent_charged), notify_msg["level"]
            )

        self.last_known_status = battery_status

    def _set_cache_timeout(self):
        self.response["cached_until"] = self.py3.time_in(self.cache_timeout)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
