# -*- coding: utf-8 -*-

"""
Display the battery level.

Configuration parameters:
    - blocks : a string, where each character represents battery level
      especially useful when using icon fonts (e.g. FontAwesome)
      default is "_▁▂▃▄▅▆▇█"
    - cache_timeout : a timeout to refresh the battery state
      default is 30
    - charging_character : a character to represent charging battery
      especially useful when using icon fonts (e.g. FontAwesome)
      default is "⚡"
    - color_bad : a color to use when the battery level is bad
      None means get it from i3status config
      default is None
    - color_charging : a color to use when the battery is charging
      None means get it from i3status config
      default is "#FCE94F"
    - color_degraded : a color to use when the battery level is degraded
      None means get it from i3status config
      default is None
    - color_good : a color to use when the battery level is good
      None means get it from i3status config
      default is None
    - format : string that formats the output. See placeholders below.
      default is "{icon}"
    - hide_when_full : hide any information when battery is fully charged
      (when the battery level is greater than or equal to 'threshold_full')
      default is False
    - notification : show current battery state as notification on click
      default is False
    - threshold_bad : a percentage at or below which the battery level should
      be considered bad
      default is 10
    - threshold_degraded : a percentage at or below which the battery level
      should be considered degraded
      default is 30
    - threshold_full : a percentage at or above which the battery level should
      should be considered full
      default is 99

Format of status string placeholders:
    {ascii_bar} - a string of ascii characters representing the battery level,
                  an alternative visualization to '{icon}' option
    {icon} - a character representing the battery level,
             as defined by the 'blocks' and 'charging_character' parameters
    {percent} - the remaining battery percentage (previously '{}')

Obsolete configuration parameters:
    - mode : an old way to define 'format' parameter. The current behavior is:
      - if 'format' is not "{icon}", this parameter is completely ignored
      - if the value is 'ascii_bar', the 'format' is set to "{ascii_bar}"
      - if the value is 'text', the 'format' is set to "Battery: {percent}"
      - all other values are ignored
      - there is no default value for this parameter
    - show_percent_with_blocks : an old way to define 'format' parameter:
      - if 'format' is not "{icon}", this parameter is completely ignored
      - if 'format' is "{icon}" and 'mode' is "ascii_bar" or "text", this
        parameter is completely ignored
      - if the value is True, the 'format' is set to "{icon} {percent}%"
      default is False

Requires:
    - the 'acpi' command line

@author shadowprince, AdamBSteele, maximbaz
@license Eclipse Public License
"""

from time import time

import math
import subprocess

BLOCKS = ["_", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
CHARGING_CHARACTER = "⚡"
EMPTY_BLOCK_CHARGING = '|'
EMPTY_BLOCK_DISCHARGING = '⍀'
FULL_BLOCK = '█'
FORMAT = "{icon}"


class Py3status:
    """
    """
    # available configuration parameters
    blocks = BLOCKS
    cache_timeout = 30
    charging_character = CHARGING_CHARACTER
    color_bad = None
    color_charging = "#FCE94F"
    color_degraded = None
    color_good = None
    format = FORMAT
    hide_when_full = False
    notification = False
    threshold_bad = 10
    threshold_degraded = 30
    threshold_full = 99
    # obsolete configuration parameters
    mode = None
    show_percent_with_blocks = False

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
        Display a notification with the remaining charge time.
        """
        if self.notification and self.time_remaining:
            subprocess.call(
                ['notify-send', '{}'.format(self.time_remaining), '-t', '4000'
                 ],
                stdout=open('/dev/null', 'w'),
                stderr=open('/dev/null', 'w'))

    def _provide_backwards_compatibility(self):
        if self.format == FORMAT:
            # Backwards compatibility for 'mode' parameter
            if self.mode == 'ascii_bar':
                self.format = "{ascii_bar}"
            elif self.mode == 'text':
                self.format = "Battery: {percent}"
            # Backwards compatibility for 'show_percent_with_blocks' parameter
            elif self.show_percent_with_blocks:
                self.format = "{icon} {percent}%"
        else:
            # Backwards compatibility for '{}' option in format string
            self.format = self.format.replace('{}', '{percent}')

    def _refresh_battery_info(self):
        # Example acpi raw output: "Battery 0: Discharging, 43%, 00:59:20 remaining"
        acpi_raw = subprocess.check_output(["acpi"], stderr=subprocess.STDOUT)
        acpi_unicode = acpi_raw.decode("UTF-8")

        #  Example list: ['Battery', '0:', 'Discharging', '43%', '00:59:20', 'remaining']
        self.acpi_list = acpi_unicode.split(' ')

        self.charging = self.acpi_list[2][:8] == "Charging"
        self.percent_charged = int(self.acpi_list[3][:-2])

    def _update_ascii_bar(self):
        ascii_bar_len = 10
        self.ascii_bar = (
            FULL_BLOCK * ((self.percent_charged * ascii_bar_len) // 100)
        ).ljust(ascii_bar_len, EMPTY_BLOCK_CHARGING if self.charging
                else EMPTY_BLOCK_DISCHARGING)

    def _update_icon(self):
        self.icon = (self.charging_character if self.charging else self.blocks[
            ((len(self.blocks) - 1) * self.percent_charged + 50) // 100])

    def _update_full_text(self):
        self.full_text = self.format.format(ascii_bar=self.ascii_bar,
                                            icon=self.icon,
                                            percent=self.percent_charged)

    def _build_response(self):
        self.response = {}

        self._set_bar_text()
        self._set_bar_color()
        self._set_cache_timeout()

        return self.response

    def _set_bar_text(self):
        self.response['full_text'] = '' if self.hide_when_full and \
            self.percent_charged >= self.threshold_full else self.full_text

    def _set_bar_color(self):
        if self.charging and self.color_charging:
            self.response['color'] = self.color_charging
        else:
            thresholds = (self.threshold_bad, self.threshold_degraded, 100)
            colors = (
                self.color_bad      or self.i3s_config['color_bad'],
                self.color_degraded or self.i3s_config['color_degraded'],
                self.color_good     or self.i3s_config['color_good'],
            )
            for threshold, color in zip(thresholds, colors):
                if self.percent_charged <= threshold:
                    self.response['color'] = color
                    break

    def _set_cache_timeout(self):
        self.response['cached_until'] = time() + self.cache_timeout


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
