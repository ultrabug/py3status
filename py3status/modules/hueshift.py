"""
Shift color temperature on the screen.

Configuration parameters:
    button_down: mouse button to decrease color temperature (default 5)
    button_toggle: mouse button to toggle color temperature (default 1)
    button_up: mouse button to increase color temperature (default 4)
    command: specify blueshift, redshift, or sct to use, otherwise auto
        (default None)
    delta: specify interval value to change color temperature (default 100)
    format: display format for this module
        *(default '{name} [\\?if=enabled&color=darkgray disabled'
        '|[\\?color=color_temperature {color_temperature}K]]')*
    maximum: specify maximum color temperature to use (default 25000)
    minimum: specify minimum color temperature to use (default 1000)
    thresholds: specify color thresholds to use
        (default [(6499, '#f6c'), (6500, '#ff6'), (6501, '#6cf')])

Control placeholders:
    {enabled} a boolean based on pgrep processing data, eg False, True

Format placeholders:
    {color_temperature} color temperature, eg 6500
    {name} name, eg Blueshift, Redshift, Sct

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    blueshift: an extensible and highly configurable alternative to redshift
    redshift: program to adjust the color temperature of your screen
    sct: set color temperature with about 40 lines of C or so

Suggestions:
    campfire: 4500
    dust storm on mars: 2000
    coffee free all nighter: 8000

Notes:
    hueshift can be disabled due to enabled running processes.
    sct and blueshift shifts only on one monitor, ideal for laptops.
    redshift shifts more than one, ideal for multi-monitors setups.

Examples:
```
# different theme
hueshift {
    format = '\\?color=color_temperature \u263c {color_temperature}K'
}

# for best results, add some limitations
hueshift {
    minimum = 3000
    maximum = 10000
}
```

@author lasers

SAMPLE OUTPUT
[{'full_text': 'Redshift '}, {'full_text': '3000K', 'color': '#ff33cc'}]

neutral
[{'full_text': 'Sct '},{'full_text': '6500K', 'color': '#ffff33'}]

cool
[{'full_text': 'Blueshift '}, {'full_text': '10000K', 'color': '#33ccff'}]
"""

STRING_BAD_COMMAND = "invalid command `{}`"
STRING_NOT_INSTALLED = "command `{}` not installed"
STRING_NOT_AVAILABLE = "no available command"


class Py3status:
    """
    """

    # available configuration parameters
    button_down = 5
    button_toggle = 1
    button_up = 4
    command = None
    delta = 100
    format = (
        r"{name} [\?if=enabled&color=darkgray disabled"
        r"|[\?color=color_temperature {color_temperature}K]]"
    )
    maximum = 25000
    minimum = 1000
    thresholds = [(6499, "#f6c"), (6500, "#ff6"), (6501, "#6cf")]

    def post_config_hook(self):
        hueshift_commands = ["sct", "blueshift", "redshift"]
        self.pgrep_command = ["pgrep", "-x", "|".join(hueshift_commands)]
        if not self.command:
            self.command = self.py3.check_commands(hueshift_commands)
        elif self.command not in hueshift_commands:
            raise Exception(STRING_BAD_COMMAND.format(self.command))
        elif not self.py3.check_commands(self.command):
            raise Exception(STRING_NOT_INSTALLED.format(self.command))
        if not self.command:
            raise Exception(STRING_NOT_AVAILABLE)

        self.hue = {
            "blueshift": lambda v: ["blueshift", "-p", "-t", format(v)],
            "redshift": lambda v: ["redshift", "-r", "-P", "-O", format(v)],
            "sct": lambda v: ["sct", format(v)],
        }
        self.name = self.command.capitalize()
        self.default = 6500
        self.maximum = min(self.maximum, 25000)
        self.minimum = max(self.minimum, 1000)
        if self.command == "sct":
            self.maximum = min(self.maximum, 10000)

        self.color_temperature = self.last_value = (
            self.py3.storage_get("color_temperature") or self.default
        )
        self.last_command = None
        self._set_color_setter_boolean()
        if not self.is_color_setter_running:
            self._set_color_temperature(delta=0)

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def _set_color_setter_boolean(self):
        # to improve user experience, we prevent users from shifting color
        # temperature when there are running processes that can also shift
        # color temperature, eg blueshift, redshift, and sct.
        try:
            self.py3.command_output(self.pgrep_command)
            self.is_color_setter_running = True
        except self.py3.CommandError:
            self.is_color_setter_running = False

    def _set_color_temperature(self, delta=None):
        value = self.color_temperature
        if delta is None:  # toggle
            if value != self.default:
                self.last_value = value
                value = self.default
            else:
                value = self.last_value
        elif delta > 0:  # scroll up
            value = min(value + self.delta, self.maximum)
        elif delta < 0:  # scroll down
            value = max(value - self.delta, self.minimum)
        command = self.hue[self.command](value)
        # skip updating at end of range
        if command != self.last_command:
            self.last_command = command
            self.py3.command_run(command)
            self.color_temperature = value
        else:
            self.py3.prevent_refresh()

    def hueshift(self):
        hue_data = {
            "name": self.name,
            "color_temperature": self.color_temperature,
            "enabled": self.is_color_setter_running,
        }

        for x in self.thresholds_init:
            if x in hue_data:
                self.py3.threshold_get_color(hue_data[x], x)

        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, hue_data),
        }

    def kill(self):
        self.py3.storage_set("color_temperature", self.color_temperature)

    def on_click(self, event):
        self._set_color_setter_boolean()
        if self.is_color_setter_running:
            return
        button = event["button"]
        if button == self.button_up:
            self._set_color_temperature(+1)
        elif button == self.button_down:
            self._set_color_temperature(-1)
        elif button == self.button_toggle:
            self._set_color_temperature()
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
