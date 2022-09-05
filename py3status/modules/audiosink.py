r"""
Display and toggle default audiosink.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 10)
    display_name_mapping: dictionary mapping devices names to display names
        (default {})
    format: display format for this module
        (default '{sinkname}')
    sinks_to_ignore: list of devices names to ignore
        (default [])

Format placeholders:
    {sinkname} short name of current default sink

Requires:
    libpulse: A featureful, general-purpose sound server (client library)

Examples:
```
audiosink {
    display_name_mapping = {"Family 17h/19h HD Audio Controller Analog Stereo": "Int", "ThinkPad Dock USB Audio Analog Stereo": "Dock"}
    format = r"{sinkname}"
    sinks_to_ignore = ["Renoir Radeon High Definition Audio Controller Digital Stereo (HDMI)"]
}
```

SAMPLE OUTPUT
{'full_text': 'Dock'}
{'full_text': 'Int'}

@author Jens Brandt <py3status@brandt-george.de>
@author AnwariasEu
@license BSD
"""

import os
import json


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    display_name_mapping = {}
    format = r"{sinkname}"
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
    # - is_default: boolean, if the device is currently the default output device
    def _get_state(self):
        sinks = json.loads(os.popen("pactl -f json list sinks").read())
        default_sink_name = os.popen("pactl get-default-sink").read().strip()
        state = [
            {
                "id": int(sink["index"]),
                "name": sink["properties"]["alsa.card_name"],
                "is_default": (sink["name"] == default_sink_name),
            }
            for sink in sinks
        ]
        # filter for not ignored (or current default) sinks
        state = list(
            filter(
                lambda d: (not d["name"] in self.sinks_to_ignore) or d["is_active"],
                state,
            )
        )
        for d in state:
            d["display_name"] = self._get_display_name(d["name"])
        return state

    def _to_string(self, state):
        default_sinkname = ""
        for s in state:
            if s["is_default"]:
                default_sinkname = s["display_name"]
                break
        return default_sinkname

    def _activate_input(self, input_id):
        os.popen(f"pactl set-default-sink {input_id}")

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
        default_sink = self.py3.composite_create(composites)
        cached_until = self.py3.time_in(self.cache_timeout)
        return {
            "cached_until": cached_until,
            "full_text": self.py3.safe_format(self.format, {"sinkname": default_sink}),
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
