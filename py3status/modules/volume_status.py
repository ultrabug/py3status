# -*- coding: utf-8 -*-
"""
Volume control.

Configuration parameters:
    button_down: button to decrease volume (default 5)
    button_mute: button to toggle mute (default 1)
    button_up: button to increase volume (default 4)
    cache_timeout: how often we refresh this module in seconds.
        (default 10)
    card: Card to use. amixer supports this. (default None)
    channel: channel to track. Default value is backend dependent.
        (default None)
    command: Choose between "amixer", "pamixer" or "pactl".
        If None, try to guess based on available commands.
        (default None)
    device: Device to use. Defaults value is backend dependent
        (default None)
    format: Format of the output.
        (default '[\?if=is_input 😮|♪]: {percentage}%')
    format_muted: Format of the output when the volume is muted.
        (default '[\?if=is_input 😶|♪]: muted')
    is_input: Is this an input device or an output device?
        (default False)
    max_volume: Allow the volume to be increased past 100% if available.
        pactl and pamixer supports this. (default 120)
    thresholds: Threshold for percent volume.
        (default [(0, 'bad'), (20, 'degraded'), (50, 'good')])
    volume_delta: Percentage amount that the volume is increased or
        decreased by when volume buttons pressed.
        (default 5)

Format placeholders:
    {percentage} Percentage volume

Color options:
    color_muted: Volume is muted, if not supplied color_bad is used
        if set to `None` then the threshold color will be used.

Requires:
    alsa-utils: an alternative implementation of linux sound support
    pamixer: pulseaudio command-line mixer like amixer

Notes:
    If you are changing volume state by external scripts etc and
    want to refresh the module quicker than the i3status interval,
    send a USR1 signal to py3status in the keybinding.
    Example: killall -s USR1 py3status

Examples:
```
# Set thresholds to rainbow colors
volume_status {
    thresholds = [
        (0, "#FF0000"),
        (10, "#E2571E"),
        (20, "#FF7F00"),
        (30, "#FFFF00"),
        (40, "#00FF00"),
        (50, "#96BF33"),
        (60, "#0000FF"),
        (70, "#4B0082"),
        (80, "#8B00FF"),
        (90, "#FFFFFF")
    ]
}
```

@author <Jan T> <jans.tuomi@gmail.com>
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u266a: 95%'}

mute
{'color': '#FF0000', 'full_text': u'\u266a: muted'}
"""

import re
from py3status.exceptions import CommandError

STRING_ERROR = "invalid command `%s`"
STRING_NOT_AVAILABLE = "no available binary"
COMMAND_NOT_INSTALLED = "command `%s` not installed"


class AudioBackend:
    def __init__(self, parent):
        self.card = parent.card
        self.channel = parent.channel
        self.device = parent.device
        self.is_input = parent.is_input
        self.parent = parent
        self.setup(parent)

    def setup(self, parent):
        raise NotImplementedError

    def run_cmd(self, cmd):
        return self.parent.py3.command_run(cmd)

    def command_output(self, cmd):
        return self.parent.py3.command_output(cmd)


class AmixerBackend(AudioBackend):
    def setup(self, parent):
        if self.card is None:
            self.card = "0"
        if self.channel is None:
            self.channel = "Capture" if self.is_input else "Master"
        if self.device is None:
            self.device = "default"
        self.cmd = [
            "amixer",
            "-q",
            "-D",
            self.device,
            "-c",
            self.card,
            "sset",
            self.channel,
        ]
        self.get_volume_cmd = [
            "amixer",
            "-M",
            "-D",
            self.device,
            "-c",
            self.card,
            "sget",
            self.channel,
        ]

    def get_volume(self):
        output = self.command_output(self.get_volume_cmd)

        # find percentage and status
        p = re.compile(r"\[(\d{1,3})%\].*\[(\w{2,3})\]")
        perc, muted = p.search(output).groups()

        # muted should be 'on' or 'off'
        if muted in ["on", "off"]:
            muted = muted == "off"
        else:
            muted = False

        return perc, muted

    def volume_up(self, delta):
        self.run_cmd(self.cmd + ["{}%+".format(delta)])

    def volume_down(self, delta):
        self.run_cmd(self.cmd + ["{}%-".format(delta)])

    def toggle_mute(self):
        self.run_cmd(self.cmd + ["toggle"])


class PamixerBackend(AudioBackend):
    def setup(self, parent):
        if self.device is None:
            self.device = "0"
        # Ignore channel
        self.channel = None
        is_input = "--source" if self.is_input else "--sink"
        self.cmd = ["pamixer", "--allow-boost", is_input, self.device]
        self.max_volume = parent.max_volume

    def get_volume(self):
        try:
            perc = self.command_output(self.cmd + ["--get-volume"])
        except CommandError as ce:
            # pamixer throws error on zero percent. see #1135
            perc = ce.output

        perc = perc.strip()
        muted = self.run_cmd(self.cmd + ["--get-mute"]) == 0
        return perc, muted

    def volume_up(self, delta):
        perc, muted = self.get_volume()
        if int(perc) + delta >= self.max_volume:
            options = ["--set-volume", str(self.max_volume)]
        else:
            options = ["-i", str(delta)]
        self.run_cmd(self.cmd + options)

    def volume_down(self, delta):
        self.run_cmd(self.cmd + ["-d", str(delta)])

    def toggle_mute(self):
        self.run_cmd(self.cmd + ["-t"])


class PactlBackend(AudioBackend):
    def setup(self, parent):
        # get available device number if not specified
        self.device_type = "source" if self.is_input else "sink"
        self.device_type_pl = self.device_type + "s"
        self.device_type_cap = self.device_type[0].upper() + self.device_type[1:]

        self.reinit_device = self.device is None
        if self.device is None:
            self.device = self.get_default_device()

        self.max_volume = parent.max_volume
        self.update_device()

    def update_device(self):
        self.re_volume = re.compile(
            r"{} \#{}.*?State: (\w+).*?Mute: (\w{{2,3}}).*?Volume:.*?(\d{{1,3}})\%".format(
                self.device_type_cap, self.device
            ),
            re.M | re.DOTALL,
        )

    def get_default_device(self):
        device_id = None

        # Find the default device for the device type
        default_dev_pattern = re.compile(
            r"^Default {}: (.*)$".format(self.device_type_cap)
        )
        output = self.command_output(["pactl", "info"])
        for info_line in output.splitlines():
            default_dev_match = default_dev_pattern.match(info_line)
            if default_dev_match is not None:
                device_id = default_dev_match.groups()[0]
                break

        # with the long gross id, find the associated number
        if device_id is not None:
            output = self.command_output(
                ["pactl", "list", "short", self.device_type_pl]
            )
            for line in output.splitlines():
                parts = line.split()
                if len(parts) < 2:
                    continue
                if parts[1] == device_id:
                    return parts[0]

        raise RuntimeError(
            "Failed to find default {} device.  Looked for {}".format(
                "input" if self.is_input else "output", device_id
            )
        )

    def get_volume(self):
        output = self.command_output(["pactl", "list", self.device_type_pl]).strip()
        try:
            state, muted, perc = self.re_volume.search(output).groups()
        except AttributeError:
            state, muted, perc = None, False, 0
            # if device is unset, try again with possibly
            # a new default device, otherwise print 0
        if self.reinit_device and state != "RUNNING":
            self.device = self.get_default_device()
            self.update_device()

        # muted should be 'on' or 'off'
        if muted in ["yes", "no"]:
            muted = muted == "yes"
        else:
            muted = False

        return perc, muted

    def volume_up(self, delta):
        perc, muted = self.get_volume()
        if int(perc) + delta >= self.max_volume:
            change = "{}%".format(self.max_volume)
        else:
            change = "+{}%".format(delta)
        self.run_cmd(
            [
                "pactl",
                "--",
                "set-{}-volume".format(self.device_type),
                self.device,
                change,
            ]
        )

    def volume_down(self, delta):
        self.run_cmd(
            [
                "pactl",
                "--",
                "set-{}-volume".format(self.device_type),
                self.device,
                "-{}%".format(delta),
            ]
        )

    def toggle_mute(self):
        self.run_cmd(
            ["pactl", "set-{}-mute".format(self.device_type), self.device, "toggle"]
        )


class Py3status:
    """
    """

    # available configuration parameters
    button_down = 5
    button_mute = 1
    button_up = 4
    cache_timeout = 10
    card = None
    channel = None
    command = None
    device = None
    format = u"[\?if=is_input 😮|♪]: {percentage}%"
    format_muted = u"[\?if=is_input 😶|♪]: muted"
    is_input = False
    max_volume = 120
    thresholds = [(0, "bad"), (20, "degraded"), (50, "good")]
    volume_delta = 5

    class Meta:
        def deprecate_function(config):
            # support old thresholds
            return {
                "thresholds": [
                    (0, "bad"),
                    (config.get("threshold_bad", 20), "degraded"),
                    (config.get("threshold_degraded", 50), "good"),
                ]
            }

        deprecated = {
            "function": [{"function": deprecate_function}],
            "remove": [
                {
                    "param": "threshold_bad",
                    "msg": "obsolete set using thresholds parameter",
                },
                {
                    "param": "threshold_degraded",
                    "msg": "obsolete set using thresholds parameter",
                },
            ],
        }

    def post_config_hook(self):
        if not self.command:
            commands = ["pamixer", "pactl", "amixer"]
            # pamixer, pactl requires pulseaudio to work
            if not self.py3.check_commands("pulseaudio"):
                commands = ["amixer"]
            self.command = self.py3.check_commands(commands)
        elif self.command not in ["amixer", "pamixer", "pactl"]:
            raise Exception(STRING_ERROR % self.command)
        elif not self.py3.check_commands(self.command):
            raise Exception(COMMAND_NOT_INSTALLED % self.command)
        if not self.command:
            raise Exception(STRING_NOT_AVAILABLE)

        # turn integers to strings
        if self.card is not None:
            self.card = "%s" % self.card
        if self.device is not None:
            self.device = "%s" % self.device
        self.volume_delta = int(self.volume_delta)

        if self.command == "amixer":
            self.backend = AmixerBackend(self)
        elif self.command == "pamixer":
            self.backend = PamixerBackend(self)
        elif self.command == "pactl":
            self.backend = PactlBackend(self)

    # compares current volume to the thresholds, returns a color code
    def _perc_to_color(self, string):
        return self.py3.threshold_get_color(string)

    # return the format string formatted with available variables
    def _format_output(self, format, percentage):
        text = self.py3.safe_format(format, {"percentage": percentage})
        return text

    def volume_status(self):
        # call backend
        perc, muted = self.backend.get_volume()

        color = None
        if muted:
            color = self.py3.COLOR_MUTED or self.py3.COLOR_BAD
        if not self.py3.is_color(color):
            # determine the color based on the current volume level
            color = self._perc_to_color(perc)

        # format the output
        text = self._format_output(self.format_muted if muted else self.format, perc)
        # create response dict
        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": color,
            "full_text": text,
        }
        return response

    def on_click(self, event):
        """
        Volume up/down and toggle mute.
        """
        button = event["button"]
        # volume up
        if button == self.button_up:
            self.backend.volume_up(self.volume_delta)
        # volume down
        elif button == self.button_down:
            self.backend.volume_down(self.volume_delta)
        # toggle mute
        elif button == self.button_mute:
            self.backend.toggle_mute()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
