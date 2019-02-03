# -*- coding: utf-8 -*-
"""
Display NumLock, CapsLock, and ScrLock keys.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    format: display format for this module
        *(default '[\?if=num_lock&color=good NUM|\?color=bad NUM] '
        '[\?if=caps_lock&color=good CAPS|\?color=bad CAPS] '
        '[\?if=scroll_lock&color=good SCR|\?color=bad SCR]')*

Control placeholders:
    {num_lock} a boolean based on xset data
    {caps_lock} a boolean based on xset data
    {scroll_lock} a boolean based on xset data

Color options:
    color_good: Lock on
    color_bad: Lock off

Examples:
```
# hide NUM, CAPS, SCR
keyboard_locks {
    format = '\?color=good [\?if=num_lock NUM][\?soft  ]'
    format += '[\?if=caps_lock CAPS][\?soft  ][\?if=scroll_lock SCR]'
}
```

@author lasers

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'NUM CAPS SCR'}

no_locks
{'color': '#FF0000', 'full_text': 'NUM CAPS SCR'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 1
    format = (
        "[\?if=num_lock&color=good NUM|\?color=bad NUM] "
        "[\?if=caps_lock&color=good CAPS|\?color=bad CAPS] "
        "[\?if=scroll_lock&color=good SCR|\?color=bad SCR]"
    )

    def post_config_hook(self):
        items = [
            "icon_num_on",
            "icon_num_off",
            "icon_caps_on",
            "icon_caps_off",
            "icon_scr_on",
            "icon_scr_off",
        ]
        if self.py3.format_contains(self.format, ["caps", "num", "scr"]) or (
            any(getattr(self, v, None) is not None for v in items)
        ):
            raise Exception("please update the config for this module")
        # end deprecation
        self.locks = {}
        self.keyring = {"num_lock": "Num", "caps_lock": "Caps", "scroll_lock": "Scroll"}

    def keyboard_locks(self):
        xset_data = self.py3.command_output("xset q")
        for k, v in self.keyring.items():
            self.locks[k] = "on" in xset_data.split("%s Lock:" % v)[1][0:6]

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, self.locks),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
