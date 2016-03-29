# -*- coding: utf-8 -*-
"""
Display the battery level.

Configuration parameters:
    battery_id: id of the battery to be displayed
        set to 'all' for combined display of all batteries
        default is 0
    blocks: a string, where each character represents battery level
        especially useful when using icon fonts (e.g. FontAwesome)
        default is "_▁▂▃▄▅▆▇█"
    cache_timeout: a timeout to refresh the battery state
        default is 30
    charging_character: a character to represent charging battery
        especially useful when using icon fonts (e.g. FontAwesome)
        default is "⚡"
    color_bad: a color to use when the battery level is bad
        None means get it from i3status config
        default is None
    color_charging: a color to use when the battery is charging
        None means get it from i3status config
        default is "#FCE94F"
    color_degraded: a color to use when the battery level is degraded
        None means get it from i3status config
        default is None
    color_good: a color to use when the battery level is good
        None means get it from i3status config
        default is None
    format: string that formats the output. See placeholders below.
        default is "{icon}"
    format_notify_charging: format of the notification received when you click
        on the module while your computer is plugged
        default is "Charging ({percent}%)"
    format_notify_discharging: format of the notification received when you
        click on the module while your comupter is not plugged
        default is "{time_remaining}"
    hide_when_full: hide any information when battery is fully charged
        default is False
    hide_seconds: hide seconds in remaining time
        default is False
    notification: show current battery state as notification on click
        default is False
    notify_low_level: display notification when battery is running low.
        default is False

Format of status string placeholders:
    {ascii_bar} - a string of ascii characters representing the battery level,
        an alternative visualization to '{icon}' option
    {icon} - a character representing the battery level,
        as defined by the 'blocks' and 'charging_character' parameters
    {percent} - the remaining battery percentage (previously '{}')
    {time_remaining} - the remaining time until the battery is empty

Obsolete configuration parameters:
    mode: an old way to define `format` parameter. The current behavior is:
        if 'format' is specified, this parameter is completely ignored
        if the value is `ascii_bar`, the `format` is set to `"{ascii_bar}"`
        if the value is `text`, the `format` is set to `"Battery: {percent}"`
        all other values are ignored
        there is no default value for this parameter
    show_percent_with_blocks: an old way to define `format` parameter:
        if `format` is specified, this parameter is completely ignored
        if the value is True, the `format` is set to `"{icon} {percent}%"`
        there is no default value for this parameter

Requires:
    - the `acpi` command line

@author shadowprince, AdamBSteele, maximbaz, 4iar
@license Eclipse Public License
"""

from __future__ import division  # python2 compatibility
from time import time
from re import findall

import math
import subprocess

BLOCKS = ["_", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
CHARGING_CHARACTER = "⚡"
EMPTY_BLOCK_CHARGING = '|'
EMPTY_BLOCK_DISCHARGING = '⍀'
FULL_BLOCK = '█'
FORMAT = "{icon}"
FORMAT_NOTIFY_CHARGING = "Charging ({percent}%)"
FORMAT_NOTIFY_DISCHARGING = "{time_remaining}"


class Py3status:
    """
    """
    # available configuration parameters
    battery_id = 0
    blocks = BLOCKS
    cache_timeout = 30
    charging_character = CHARGING_CHARACTER
    color_bad = None
    color_charging = "#FCE94F"
    color_degraded = None
    color_good = None
    format = FORMAT
    format_notify_charging = FORMAT_NOTIFY_CHARGING
    format_notify_discharging = FORMAT_NOTIFY_DISCHARGING
    hide_when_full = False
    hide_seconds = False
    notification = False
    notify_low_level = False
    # obsolete configuration parameters
    mode = None
    show_percent_with_blocks = None

    def battery_level(self, i3s_output_list, i3s_config):
        self.i3s_config = i3s_config
        self.i3s_output_list = i3s_output_list

        self._refresh_battery_info()

        self._provide_backwards_compatibility()
        self._update_icon()
        self._update_ascii_bar()
        self._update_full_text()

        return self._build_response()

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Display a notification following the specified format
        """
        if not self.notification:
            return

        if self.time_remaining:
            format = self.format_notify_discharging
        else:
            format = self.format_notify_charging

        message = format.format(ascii_bar=self.ascii_bar, icon=self.icon,
                                percent=self.percent_charged,
                                time_remaining=self.time_remaining)

        if message:
            self._desktop_notification(message)

    def _desktop_notification(self, message):
        """
        Display the given message inside a desktop notification
        """
        subprocess.call(
            ['notify-send', '{}'.format(message), '-t',
                '4000'],
            stdout=open('/dev/null', 'w'),
            stderr=open('/dev/null', 'w'))

    def _provide_backwards_compatibility(self):
        # Backwards compatibility for 'mode' parameter
        if self.format == FORMAT and self.mode == 'ascii_bar':
            self.format = "{ascii_bar}"
        if self.format == FORMAT and self.mode == 'text':
            self.format = "Battery: {percent}"

        # Backwards compatibility for 'show_percent_with_blocks' parameter
        if self.format == FORMAT and self.show_percent_with_blocks:
            self.format = "{icon} {percent}%"

        # Backwards compatibility for '{}' option in format string
        self.format = self.format.replace('{}', '{percent}')

    def _extract_battery_information_from_acpi(self, acpi_battery_lines):
        """
        Extract the percent charged, charging state, time remaining,
        and capacity for a battery, given a list of two strings from acpi
        """
        battery = dict()
        battery["percent_charged"] = int(findall("(?<= )(\d+)(?=%)",
                                                 acpi_battery_lines[0])[0])
        battery["charging"] = "Charging" in acpi_battery_lines[0]
        battery["capacity"] = int(findall("(?<= )(\d+)(?= mAh)",
                                          acpi_battery_lines[1])[1])

        # ACPI only shows time remaining if battery is discharging or charging
        try:
            battery["time_remaining"] = ''.join(findall(
                "(?<=, )(\d+:\d+:\d+)(?= remaining)|"
                "(?<=, )(\d+:\d+:\d+)(?= until)", acpi_battery_lines[0])[0])
            if self.hide_seconds:
                battery["time_remaining"] = battery["time_remaining"][:-3]
        except IndexError:
            battery["time_remaining"] = '?'

        return battery

    def _hms_to_seconds(self, t):
        h, m, s = [int(i) for i in t.split(':')]
        return 3600 * h + 60 * m + s

    def _seconds_to_hms(self, secs):
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    def _refresh_battery_info(self):
        # Example acpi -bi raw output:
        #      "Battery 0: Discharging, 94%, 09:23:28 remaining
        #       Battery 0: design capacity 5703 mAh, last full capacity 5283 mAh = 92%
        #       Battery 1: Unknown, 98%
        #       Battery 1: design capacity 1880 mAh, last full capacity 1370 mAh = 72%"
        acpi_raw = subprocess.check_output(
            ["acpi", "-b", "-i"],
            stderr=subprocess.STDOUT)

        #  Example list:
        #       ['Battery 0: Charging, 96%, 00:20:40 until charged',
        #       'Battery 0: design capacity 5566 mAh, last full capacity 5156 mAh = 92%',
        #       'Battery 1: Unknown, 98%',
        #       'Battery 1: design capacity 1879 mAh, last full capacity 1370 mAh = 72%',
        #       '']
        acpi_list = acpi_raw.decode("UTF-8").split('\n')

        # Separate the output because each pair of lines corresponds to a single battery.
        # Now the list index will correspond to the index of the battery we want to look at
        acpi_list = [acpi_list[i:i + 2]
                     for i in range(0, len(acpi_list) - 1, 2)]

        battery_list = [self._extract_battery_information_from_acpi(battery)
                        for battery in acpi_list]

        if type(self.battery_id) == int:
            battery = battery_list[self.battery_id]
            self.percent_charged = battery['percent_charged']
            self.charging = battery['charging']
            self.time_remaining = battery['time_remaining']

        elif self.battery_id == "all":
            total_capacity = sum([battery['capacity'] for battery in
                                  battery_list])

            # Average and weigh % charged by the capacities of the batteries so that self.percent_charged
            # properly represents batteries that have different capacities.
            self.percent_charged = int(sum([battery[
                "capacity"] / total_capacity * battery["percent_charged"]
                                            for battery in battery_list]))

            self.charging = any([battery["charging"] for battery in
                                 battery_list])

            # Assumes a system has at max two batteries
            active_battery = None
            inactive_battery = battery_list[:]
            for battery_id in range(0, len(battery_list)):
                if battery_list[battery_id]["time_remaining"]:
                    active_battery = battery_list[battery_id]
                    del inactive_battery[battery_id]

            # Only one battery will be discharging or charging at a time.
            # Therefore, ACPI does not provide a time remaining value for the other battery.
            # So the time remaining for the other battery is calculated using the time
            # remaining of the first battery and the capacity values for both batteries.
            if active_battery and inactive_battery:
                inactive_battery = inactive_battery[0]

                time_remaining_seconds = self._hms_to_seconds(active_battery[
                    "time_remaining"])
                rate_second_per_mah = time_remaining_seconds / (
                    active_battery["capacity"] *
                    (active_battery["percent_charged"] / 100))
                time_remaining_seconds += inactive_battery["capacity"] * \
                    inactive_battery["percent_charged"]/100 * rate_second_per_mah

                self.time_remaining = self._seconds_to_hms(
                    time_remaining_seconds)

            elif active_battery:
                self.time_remaining = active_battery["time_remaining"]

            else:
                self.time_remaining = None

    def _update_ascii_bar(self):
        self.ascii_bar = FULL_BLOCK * int(self.percent_charged / 10)
        if self.charging:
            self.ascii_bar += EMPTY_BLOCK_CHARGING * (
                10 - int(self.percent_charged / 10))
        else:
            self.ascii_bar += EMPTY_BLOCK_DISCHARGING * (
                10 - int(self.percent_charged / 10))

    def _update_icon(self):
        if self.charging:
            self.icon = self.charging_character
        else:
            self.icon = self.blocks[int(math.ceil(self.percent_charged / 100 *
                                                  (len(self.blocks) - 1)))]

    def _update_full_text(self):
        self.full_text = self.format.format(ascii_bar=self.ascii_bar,
                                            icon=self.icon,
                                            percent=self.percent_charged,
                                            time_remaining=self.time_remaining)

    def _build_response(self):
        self.response = {}

        self._set_bar_text()
        self._set_bar_color()
        self._set_cache_timeout()

        return self.response

    def _set_bar_text(self):
        if self.percent_charged == 100 and self.hide_when_full:
            self.response['full_text'] = ''
        else:
            self.response['full_text'] = self.full_text

    def _set_bar_color(self):
        if self.charging:
            self.response['color'] = self.color_charging
            battery_status = 'charging'
        elif self.percent_charged < 10:
            self.response['color'] = self.color_bad or self.i3s_config[
                'color_bad']
            battery_status = 'bad'
            if self.notify_low_level and self.last_known_status != battery_status:
                self._notify('Battery level is critically low ({}%)',
                             'critical')
        elif self.percent_charged < 30:
            self.response['color'] = self.color_degraded or self.i3s_config[
                'color_degraded']
            battery_status = 'degraded'
            if self.notify_low_level and self.last_known_status != battery_status:
                self._notify('Battery level is running low ({}%)', 'normal')
        elif self.percent_charged == 100:
            self.response['color'] = self.color_good or self.i3s_config[
                'color_good']
            battery_status = 'full'
        else:
            battery_status = 'good'
        self.last_known_status = battery_status

    def _set_cache_timeout(self):
        self.response['cached_until'] = time() + self.cache_timeout

    def _notify(self, text, urgency):
        subprocess.call(
            ['notify-send', text.format(self.percent_charged), '-u', urgency],
            stdout=open('/dev/null', 'w'),
            stderr=open('/dev/null', 'w'))


if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00',
    }
    while True:
        print(x.battery_level([], config))
        sleep(1)
