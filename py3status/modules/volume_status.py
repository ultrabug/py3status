"""
Volume control.

Configuration parameters:
    blocks: a string, where each character represents a volume level
            (default "_▁▂▃▄▅▆▇█")
    button_down: button to decrease volume (default 5)
    button_mute: button to toggle mute (default 1)
    button_up: button to increase volume (default 4)
    cache_timeout: how often we refresh this module in seconds.
        (default 10)
    card: Card to use. amixer supports this. (default None)
    channel: channel to track. Default value is backend dependent.
        (default None)
    command: Choose between "amixer", "pamixer", "pactl" or "wpctl".
        If None, try to guess based on available commands.
        (default None)
    device: Device to use. Defaults value is backend dependent.
        "aplay -L", "pactl list sinks short", "pamixer --list-sinks", "wpctl status -n"
        (default None)
    format: Format of the output.
        (default '[\\?if=is_input 😮|♪]: {percentage}%')
    format_muted: Format of the output when the volume is muted.
        (default '[\\?if=is_input 😶|♪]: muted')
    is_input: Is this an input device or an output device?
        (default False)
    max_volume: Allow the volume to be increased past 100% if available.
        pactl, pamixer and wpctl support this. (default 120)
    thresholds: Threshold for percent volume.
        (default [(0, 'bad'), (20, 'degraded'), (50, 'good')])
    volume_delta: Percentage amount that the volume is increased or
        decreased by when volume buttons pressed.
        (default 5)

Format placeholders:
    {icon} Character representing the volume level,
            as defined by the 'blocks'
    {percentage} Percentage volume

Color options:
    color_muted: Volume is muted, if not supplied color_bad is used
        if set to `None` then the threshold color will be used.

Requires:
    alsa-utils: an alternative implementation of linux sound support
    pamixer: pulseaudio command-line mixer like amixer
    wireplumber: provides wpctl, the PipeWire session manager control tool

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

import math
import re
from time import sleep

from py3status.exceptions import CommandError

STRING_ERROR = "invalid command `{}`"
STRING_NOT_AVAILABLE = "no available binary"
COMMAND_NOT_INSTALLED = "command `{}` not installed"


class Audio:
    def __init__(self, parent):
        self.card = parent.card
        self.channel = parent.channel
        self.device = parent.device
        self.is_input = parent.is_input
        self.max_volume = parent.max_volume
        self.parent = parent
        self.setup(parent)

    def setup(self, parent):
        raise NotImplementedError

    def run_cmd(self, cmd):
        return self.parent.py3.command_run(cmd)

    def command_output(self, cmd):
        return self.parent.py3.command_output(cmd)


class Amixer(Audio):
    def setup(self, parent):
        if self.card is None:
            self.card = "0"
        if self.device is None:
            self.device = "default"
        if self.channel is None:
            controls = self.parent.py3.command_output(
                ["amixer", "-c", self.card, "-D", self.device, "scontrols"]
            ).splitlines()
            self.channel = controls[-abs(int(self.is_input))].split("'")[1::2][0]
        self.cmd = [
            "amixer",
            "-M",
            "-q",
            "-c",
            self.card,
            "-D",
            self.device,
            "sset",
            self.channel,
        ]
        self.get_volume_cmd = [
            "amixer",
            "-M",
            "-c",
            self.card,
            "-D",
            self.device,
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
        self.run_cmd(self.cmd + [f"{delta}%+"])

    def volume_down(self, delta):
        self.run_cmd(self.cmd + [f"{delta}%-"])

    def toggle_mute(self):
        self.run_cmd(self.cmd + ["toggle"])


class Pamixer(Audio):
    def setup(self, parent):
        if self.device is not None:
            dev_target = ["--source" if self.is_input else "--sink", self.device]
        elif self.is_input:
            dev_target = ["--default-source"]
        else:
            dev_target = []
        self.cmd = ["pamixer", "--allow-boost"] + dev_target

    def get_volume(self):
        try:
            line = self.command_output(self.cmd + ["--get-mute", "--get-volume"])
        except CommandError as ce:
            # pamixer throws error on zero percent. see #1135
            line = ce.output
        try:
            muted, perc = line.split()
            muted = muted == "true"
        except ValueError:
            muted, perc = None, None
        return perc, muted

    def volume_up(self, delta):
        perc, muted = self.get_volume()
        if int(perc) + delta >= self.max_volume:
            options = ["--set-volume", str(self.max_volume)]
        else:
            options = ["--increase", str(delta)]
        self.run_cmd(self.cmd + options)

    def volume_down(self, delta):
        self.run_cmd(self.cmd + ["--decrease", str(delta)])

    def toggle_mute(self):
        self.run_cmd(self.cmd + ["--toggle-mute"])


class Pactl(Audio):
    def setup(self, parent):
        # get available device number if not specified
        self.detected_devices = {}
        self.device_type = "source" if self.is_input else "sink"
        self.device_type_pl = self.device_type + "s"
        self.device_type_cap = self.device_type[0].upper() + self.device_type[1:]

        self.use_default_device = self.device is None
        if self.use_default_device:
            self.device = self.get_default_device()
        else:
            # if a device name was present but is used to match multiple
            # possible devices sharing the same name pattern we allow ourselves
            # to override the device name
            self.set_selected_device()
        self.update_device()

    def update_device(self):
        self.re_volume = re.compile(
            r"{} (?:#{}|.*?Name: {}).*?Mute: (\w{{2,3}}).*?Volume:.*?(\d{{1,3}})%".format(
                self.device_type_cap, self.device, self.device
            ),
            re.M | re.DOTALL,
        )

    def get_default_device(self):
        device_id = None

        # Find the default device for the device type
        default_dev_pattern = re.compile(rf"^Default {self.device_type_cap}: (.*)$")
        output = self.command_output(["pactl", "info"])
        for info_line in output.splitlines():
            default_dev_match = default_dev_pattern.match(info_line)
            if default_dev_match is not None:
                device_id = default_dev_match.groups()[0]
                break

        # with the long gross id, find the associated number
        if device_id is not None:
            for d_number, d_id in self.get_current_devices().items():
                if d_id == device_id:
                    return d_number

        raise RuntimeError(
            "Failed to find default {} device.  Looked for {}".format(
                "input" if self.is_input else "output", device_id
            )
        )

    def set_selected_device(self):
        current_devices = self.get_current_devices()
        if self.device in current_devices.values():
            return
        for device_name in current_devices.values():
            if self.device in device_name:
                self.parent.py3.log(f"device {self.device} detected as {device_name}")
                self.device = device_name
                break

    def get_current_devices(self):
        current_devices = {}
        output = self.command_output(["pactl", "list", "short", self.device_type_pl])
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            current_devices[parts[0]] = parts[1]
        if current_devices != self.detected_devices:
            self.detected_devices = current_devices
            self.parent.py3.log(f"available {self.device_type_pl}: {current_devices}")
        return current_devices

    def get_volume(self):
        output = self.command_output(["pactl", "list", self.device_type_pl]).strip()
        if self.use_default_device:
            self.device = self.get_default_device()
            self.update_device()
        try:
            muted, perc = self.re_volume.search(output).groups()
            muted = muted == "yes"
        except AttributeError:
            muted, perc = None, None
        return perc, muted

    def volume_up(self, delta):
        perc, muted = self.get_volume()
        if int(perc) + delta >= self.max_volume:
            change = f"{self.max_volume}%"
        else:
            change = f"+{delta}%"
        self.run_cmd(["pactl", "--", f"set-{self.device_type}-volume", self.device, change])

    def volume_down(self, delta):
        self.run_cmd(
            [
                "pactl",
                "--",
                f"set-{self.device_type}-volume",
                self.device,
                f"-{delta}%",
            ]
        )

    def toggle_mute(self):
        self.run_cmd(["pactl", f"set-{self.device_type}-mute", self.device, "toggle"])


class Wpctl(Audio):
    def setup(self, parent):
        self.device_re = re.compile(r"(?P<id>\d+)\.\s+(?P<name>.+)$")
        self.volume_re = re.compile(r"\[vol:\s*(?P<volume>[0-9.]+)(?:\s+(?P<muted>MUTED))?\]")

        self.max_volume = f"{self.max_volume / 100}"

        self.selected_device_category = "Sources" if self.is_input else "Sinks"
        if not self.device:
            self.selected_device_id = (
                "@DEFAULT_AUDIO_SOURCE@" if self.is_input else "@DEFAULT_AUDIO_SINK@"
            )

    def get_volume(self):
        device = self._get_selected_device()
        if not device:
            return None, None
        return device["volume"], device["muted"]

    def volume_up(self, delta):
        device_id = self._get_selected_device_id()
        if device_id:
            # wpctl clamps to 100% unless an explicit limit is passed
            self.run_cmd(["wpctl", "set-volume", "-l", self.max_volume, device_id, f"{delta}%+"])

    def volume_down(self, delta):
        device_id = self._get_selected_device_id()
        if device_id:
            self.run_cmd(["wpctl", "set-volume", device_id, f"{delta}%-"])

    def toggle_mute(self):
        device_id = self._get_selected_device_id()
        if device_id:
            self.run_cmd(["wpctl", "set-mute", device_id, "toggle"])

    def _get_selected_device_id(self):
        if not self.device:
            return self.selected_device_id
        device = self._get_selected_device()
        return device["id"] if device else None

    def _get_wpctl_status_output(self):
        return self.command_output(["wpctl", "status", "-n"])

    def _get_selected_device(self):
        if not self.device:
            return self._get_default_device()

        status_output = self._get_wpctl_status_output()
        for device in self._get_audio_devices(status_output):
            if device["name"] == self.device:
                return device
        return None

    def _get_audio_devices(self, status):
        devices = []

        for chunk in status.split("\n\n"):
            lines = chunk.splitlines()
            if not lines or lines[0].strip() != "Audio":
                continue

            in_category = False
            for raw_line in lines[1:]:
                line = raw_line.lstrip(" │├─")
                if not line:
                    continue
                if line.endswith(":"):
                    in_category = line[:-1] == self.selected_device_category
                    continue
                if not in_category:
                    continue

                volume_match = self.volume_re.search(line)
                if not volume_match:
                    continue
                match = self.device_re.match(line[: volume_match.start()].strip(" *"))
                if not match:
                    continue

                devices.append(
                    {
                        "id": match.group("id"),
                        "muted": bool(volume_match.group("muted")),
                        "name": match.group("name"),
                        "volume": self._format_volume(volume_match.group("volume")),
                    }
                )
            break
        return devices

    def _get_default_device(self):
        parts = (
            self.command_output(["wpctl", "get-volume", self.selected_device_id]).lower().split()
        )
        try:
            return {
                "volume": self._format_volume(parts[1]),
                "muted": "[muted]" in parts,
            }
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _format_volume(volume):
        return int(float(volume) * 100)


class Py3status:
    """"""

    # available configuration parameters
    blocks = "_▁▂▃▄▅▆▇█"
    button_down = 5
    button_mute = 1
    button_up = 4
    cache_timeout = 10
    card = None
    channel = None
    command = None
    device = None
    format = r"[\?if=is_input 😮|♪]: {percentage}%"
    format_muted = r"[\?if=is_input 😶|♪]: muted"
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
                {
                    "param": "start_delay",
                    "msg": "obsolete parameter",
                },
            ],
        }

    def post_config_hook(self):
        if not self.command:
            commands = ["pamixer", "pactl", "amixer", "wpctl"]
            # pamixer, pactl requires pulseaudio to work
            if not self.py3.check_commands(["pulseaudio", "pipewire"]):
                commands = ["amixer"]
            self.command = self.py3.check_commands(commands)
        elif self.command not in ["amixer", "pamixer", "pactl", "wpctl"]:
            raise Exception(STRING_ERROR.format(self.command))
        elif not self.py3.check_commands(self.command):
            raise Exception(COMMAND_NOT_INSTALLED.format(self.command))
        if not self.command:
            raise Exception(STRING_NOT_AVAILABLE)

        # turn integers to strings
        if self.card is not None:
            self.card = str(self.card)
        if self.device is not None:
            self.device = str(self.device)

        self._init_backend()
        self.color_muted = self.py3.COLOR_MUTED or self.py3.COLOR_BAD

    def _init_backend(self):
        # attempt it a few times since the audio service may still be loading during startup
        for i in range(6):
            try:
                self.backend = globals()[self.command.capitalize()](self)
                return
            except Exception:  # noqa e722
                # try again later (exponential backoff)
                sleep(0.5 * 2**i)

        self.backend = globals()[self.command.capitalize()](self)

    def volume_status(self):
        perc, muted = self.backend.get_volume()
        color = None
        icon = None
        new_format = self.format

        if perc is None:
            perc = "?"
        elif muted:
            color = self.color_muted
            new_format = self.format_muted
        else:
            color = self.py3.threshold_get_color(perc)
            icon = self.blocks[
                min(
                    len(self.blocks) - 1,
                    math.ceil(int(perc) / 100 * (len(self.blocks) - 1)),
                )
            ]

        volume_data = {"icon": icon, "percentage": perc}

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(new_format, volume_data),
            "color": color,
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_up:
            try:
                self.backend.volume_up(self.volume_delta)
            except TypeError:
                pass
        elif button == self.button_down:
            self.backend.volume_down(self.volume_delta)
        elif button == self.button_mute:
            self.backend.toggle_mute()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        "format": r"[\?if=is_input SOURCE|SINK] \[{command}\] \[{device}\] " + Py3status.format,
        "format_muted": r"[\?if=is_input SOURCE|SINK] \[{command}\] \[{device}\] "
        + Py3status.format_muted,
        "command": "wpctl",
        # "device": "alsa_output.usb-0d8c_USB_PnP_Sound_Device-00.analog-stereo",
        # "is_input": True,
    }
    from py3status.module_test import module_test

    module_test(Py3status, config=config)
