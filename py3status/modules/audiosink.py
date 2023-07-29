r"""
Display and toggle default audiosink.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 10)
    display_name_mapping: dictionary mapping devices names to display names
        (default {})
    format: display format for this module
        (default '{audiosink}')
    sinks_to_ignore: list of devices names to ignore
        (default [])

Format placeholders:
    {audiosink} comma seperated list of (display) names of default sink(s)

Requires:
    pulseaudio: networked sound server

Examples:
```
audiosink {
    display_name_mapping = {"Family 17h/19h HD Audio Controller Analog Stereo": "Int", "ThinkPad Dock USB Audio Analog Stereo": "Dock"}
    format = r"{audiosink}"
    sinks_to_ignore = ["Renoir Radeon High Definition Audio Controller Digital Stereo (HDMI)"]
}
```

@author Jens Brandt <py3status@brandt-george.de>
@license BSD

SAMPLE OUTPUT
{'full_text': 'Dock'}

int
{'full_text': 'Int'}
"""

import os


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    display_name_mapping = {}
    format = r"{audiosink}"
    sinks_to_ignore = []

    def _get_display_name(self, name):
        if name in self.display_name_mapping:
            return self.display_name_mapping[name]
        return name

    # returns list of (not ignored) audiosinks
    # each audiosink is given by the dictionary keys:
    # - id: pulseaudio id of the device
    # - name: device name
    # - display_name: display name as given by display_name_mapping
    # - is_active: boolean, if the device is currently the default output device
    def _get_state(self):
        # The following two commands are a very dirty way of getting the required information from the pacmd text output.
        # I'd love to see pulseaudio / pacmd support in jc, so this can be done more pretty.
        pacmd_output = (
            os.popen("pacmd list-sinks | grep -e 'device.description' -e 'index:'")
            .read()
            .split("\n")
        )
        state = [
            {
                "id": int(pacmd_output[i][-1]),
                "name": pacmd_output[i + 1].split('"')[1],
                "is_active": ("*" in pacmd_output[i]),
            }
            for i in range(0, len(pacmd_output) - 1, 2)
        ]
        # filter for not ignored (or active) devices
        state = list(
            filter(
                lambda d: (d["name"] not in self.sinks_to_ignore) or d["is_active"],
                state,
            )
        )
        for d in state:
            d["display_name"] = self._get_display_name(d["name"])
        return state

    def _to_string(self, state):
        return ", ".join([s["display_name"] for s in state if s["is_active"]])

    def _activate_input(self, input_id):
        os.popen(f"pacmd set-default-sink {input_id}")

    # activates the next devices following the first currently active device
    def _toggle(self, state):
        for i in range(len(state)):
            if state[i]["is_active"]:
                input_to_activate_index = (i + 1) % len(state)
                self._activate_input(state[input_to_activate_index]["id"])
                return

    def audiosink(self):
        composites = [
            {"full_text": self._to_string(self._get_state())},
        ]
        audiosink = self.py3.composite_create(composites)
        cached_until = self.py3.time_in(self.cache_timeout)
        return {
            "cached_until": cached_until,
            "full_text": self.py3.safe_format(self.format, {"audiosink": audiosink}),
        }

    def on_click(self, event):
        button = event["button"]
        if button == 1:
            self._toggle(self._get_state())


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
