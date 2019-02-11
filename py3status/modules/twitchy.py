# -*- coding: utf-8 -*-
"""
Display channels currently streaming on Twitch.tv.

Configuration parameters:
    button_next: mouse button to display next channel (default 4)
    button_open: mouse button to open current channel (default 1)
    button_previous: mouse button to display previous channel (default 5)
    cache_timeout: refresh interval for this module (default 60)
    format: display format for this module
        (default '{format_channel}|No Twitchy')
    format_channel: display format for this channel
        *(default "{channelaltname} [\?color=violet {gamealtname}]"
        "[\?color=darkgray [ {viewers}][ {uptime}]]")*
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {format_channel} format for channels
    {channel}        total number of channels, eg 10

format_channel placeholders:
    {gamename}       eg py3status
    {gamealtname}    eg py3status
    {channelname}    eg ultrabug
    {channelaltname} eg Ultrabug
    {status}         eg I love bugs.
    {viewers}        eg 55
    {uptime}         eg 2h25m

    See `NON-INTERACTIVE` in `twitchy.cfg` for a list of Twitchy
    placeholders to enable. Not all of placeholders will be enabled.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    twitchy: cli streamlink wrapper for twitch.tv
    https://github.com/BasioMeusPuga/twitchy

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'Ultrabug ', 'color': '#ee82ee'},
    {'full_text': 'Monster Bug Hunter 8h43m '},
    {'full_text': '1', 'color': '#a9a9a9'},
]

tobes
[
    {'full_text': 'tobes ', 'color': '#ee82ee'},
    {'full_text': 'Snake Eater 6h38m '},
    {'full_text': '2', 'color': '#a9a9a9'},
]

lasers
[
    {'full_text': 'lasers ', 'color': '#ee82ee'},
    {'full_text': 'Laser Light Show 3h40m '},
    {'full_text': '3', 'color': '#a9a9a9'},
]

maximbaz
[
    {'full_text': 'MaximBaz ', 'color': '#ee82ee'},
    {'full_text': 'Hitman 1h18m '},
    {'full_text': '4', 'color': '#a9a9a9'},
]
"""

from os import path
from time import time

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_open = 1
    button_previous = 5
    cache_timeout = 60
    format = "{format_channel}|No Twitchy"
    format_channel = (
        "{channelaltname} [\?color=violet {gamealtname}]"
        "[\?color=darkgray [ {viewers}][ {uptime}]]"
    )
    thresholds = []

    def post_config_hook(self):
        if not self.py3.check_commands("twitchy"):
            raise Exception(STRING_NOT_INSTALLED)

        self.active_index = 0
        self.button_refresh = 2
        self.channel_data = {}
        self.delimiter = "|DELIMITER|"
        self.idle_time = 0
        self.scrolling = False
        self.twitchy_command = [
            "twitchy",
            "--non-interactive",
            "--delimiter",
            self.delimiter,
        ]
        self.empty_defaults = {
            x: None for x in self.py3.get_placeholders_list(self.format)
        }

        self.placeholders = []
        with open(path.expanduser("~/.config/twitchy3/twitchy.cfg")) as f:
            for line in reversed(f.readlines()):
                if "DisplayScheme =" in line:
                    placeholders = line.split("=")[-1].lower().split(",")
                    self.placeholders = [x.strip() for x in placeholders]
                    break

        self.thresholds_init = {}
        for name in ["format", "format_channel"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def _get_twitchy_data(self):
        try:
            return self.py3.command_output(self.twitchy_command).strip()
        except self.py3.CommandError:
            return ""

    def _manipulate(self, data):
        new_data = {}
        for index, line in enumerate(data.splitlines()):
            channel = dict(zip(self.placeholders, line.split(self.delimiter)))
            channel["index"] = index + 1
            if "uptime" in channel:
                channel["uptime"] = channel["uptime"].replace(" ", "")
            format_channel = self.py3.safe_format(self.format_channel, channel)
            self.py3.composite_update(format_channel, {"index": channel["channelname"]})

            for x in self.thresholds_init["format_channel"]:
                if x in channel:
                    self.py3.threshold_get_color(channel[x], x)
            new_data[index] = channel

        return new_data

    def twitchy(self):
        # refresh
        current_time = time()
        refresh = current_time >= self.idle_time

        # time
        if refresh:
            self.idle_time = current_time + self.cache_timeout
            cached_until = self.cache_timeout
        else:
            cached_until = self.idle_time - current_time

        # button
        if self.scrolling and not refresh:
            self.scrolling = False
            data = self.channel_data
        else:
            data = self._manipulate(self._get_twitchy_data())
            self.channel_data = data

        if data:
            self.count_channels = len(data)
            channel = data.get(self.active_index, {})
            format_channel = self.py3.safe_format(self.format_channel, channel)
            self.py3.composite_update(format_channel, {"index": channel["channelname"]})

            twitchy_data = {
                "format_channel": format_channel,
                "channel": self.count_channels,
            }

            for x in self.thresholds_init["format"]:
                if x in twitchy_data:
                    self.py3.threshold_get_color(twitchy_data[x], x)
        else:
            twitchy_data = self.empty_defaults

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, twitchy_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button in [self.button_next, self.button_previous]:
            if self.channel_data:
                self.scrolling = True
                if button == self.button_next:
                    self.active_index += 1
                elif button == self.button_previous:
                    self.active_index -= 1
                self.active_index %= self.count_channels
            else:
                self.py3.prevent_refresh()
        elif button == self.button_refresh:
            self.idle_time = 0
        else:
            if button == self.button_open:
                index = event["index"]
                if not isinstance(index, int):
                    command = "twitchy --non-interactive kickstart {name}"
                    self.py3.command_run(command.format(name=index))
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
