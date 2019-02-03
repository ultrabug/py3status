# -*- coding: utf-8 -*-
"""
Display a fortune-telling, swimming fish.

Wanda has no use what-so-ever. It only takes up disk space and compilation time,
and if loaded, it also takes up precious bar space, memory, and cpu cycles.
Anybody found using it should be promptly sent for a psychiatric evaluation.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 0)
    format: display format for this module
        (default '{nomotion}[{fortune} ]{wanda}{motion}')
    fortune_timeout: refresh interval for fortune (default 60)

Format placeholders:
    {fortune} one of many aphorisms or vague prophecies
    {wanda} name of one of the most commonly kept freshwater aquarium fish
    {motion} biologically propelled motion through a liquid medium
    {nomotion} opposite behavior of motion to prevent modules from shifting

Optional:
    fortune-mod: the fortune cookie program from bsd games

Examples:
```
# disable motions when not in use
wanda_the_fish {
    format = '[\?if=fortune {nomotion}][{fortune} ]'
    format += '{wanda}[\?if=fortune {motion}]'
}

# no updates, no motions, yes fortunes, you click
wanda_the_fish {
    format = '[{fortune} ]{wanda}'
    cache_timeout = -1
}

# wanda moves, fortunes stays
wanda_the_fish {
    format = '[{fortune} ]{nomotion}{wanda}{motion}'
}

# wanda is swimming too fast, slow down wanda
wanda_the_fish {
    cache_timeout = 2
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'innovate, v.: To annoy people.'},
    {'full_text': ' <', 'color': '#ffa500'},
    {'full_text': '\xba', 'color': '#add8e6'},
    {'full_text': ',', 'color': '#ff8c00'},
    {'full_text': '))', 'color': '#ffa500'},
    {'full_text': '))>< ', 'color': '#ff8c00'},
]

idle
[
    {'full_text': ' <', 'color': '#ffa500'},
    {'full_text': '\xba', 'color': '#add8e6'},
    {'full_text': ',', 'color': '#ff8c00'},
    {'full_text': '))', 'color': '#ffa500'},
    {'full_text': '))>3', 'color': '#ff8c00'},
]

py3status
[
    {'full_text': 'py3status is so cool!'},
    {'full_text': ' <', 'color': '#ffa500'},
    {'full_text': '\xba', 'color': '#add8e6'},
    {'full_text': ',', 'color': '#ff8c00'},
    {'full_text': '))', 'color': '#ffa500'},
    {'full_text': '))>< ', 'color': '#ff8c00'},
]
"""

from time import time


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 0
    format = "{nomotion}[{fortune} ]{wanda}{motion}"
    fortune_timeout = 60

    def post_config_hook(self):
        body = (
            "[\?color=orange&show <"
            "[\?color=lightblue&show º]"
            "[\?color=darkorange&show ,]))"
            "[\?color=darkorange&show ))>%s]]"
        )
        wanda = [body % fin for fin in ("<", ">", "<", "3")]
        self.wanda = [self.py3.safe_format(x) for x in wanda]
        self.wanda_length = len(self.wanda)
        self.index = 0

        self.fortune_command = ["fortune", "-as"]
        self.fortune = self.py3.storage_get("fortune") or None
        self.toggled = self.py3.storage_get("toggled") or False
        self.motions = {"motion": " ", "nomotion": ""}

        # deal with {new,old} timeout between storage
        fortune_timeout = self.py3.storage_get("fortune_timeout")
        timeout = None
        if self.fortune_timeout != fortune_timeout:
            timeout = time() + self.fortune_timeout
        self.time = (
            timeout or self.py3.storage_get("time") or (time() + self.fortune_timeout)
        )

    def _set_fortune(self, state=None, new=False):
        if not self.fortune_command:
            return
        if new:
            try:
                fortune_data = self.py3.command_output(self.fortune_command)
            except self.py3.CommandError:
                self.fortune = ""
                self.fortune_command = None
            else:
                self.fortune = " ".join(fortune_data.split())
                self.time = time() + self.fortune_timeout
        elif state is None:
            if self.toggled and time() >= self.time:
                self._set_fortune(new=True)
        else:
            self.toggled = state
            if state:
                self._set_fortune(new=True)
            else:
                self.fortune = None

    def _set_motion(self):
        for k in self.motions:
            self.motions[k] = "" if self.motions[k] else " "

    def _set_wanda(self):
        self.index += 1
        if self.index >= self.wanda_length:
            self.index = 0

    def wanda_the_fish(self):
        self._set_fortune()
        self._set_motion()
        self._set_wanda()

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format,
                {
                    "fortune": self.fortune,
                    "motion": self.motions["motion"],
                    "nomotion": self.motions["nomotion"],
                    "wanda": self.wanda[self.index],
                },
            ),
        }

    def kill(self):
        self.py3.storage_set("toggled", self.toggled)
        self.py3.storage_set("fortune", self.fortune)
        self.py3.storage_set("fortune_timeout", self.fortune_timeout)
        self.py3.storage_set("time", self.time)

    def on_click(self, event):
        if not self.fortune_command:
            return
        self._set_fortune(not self.toggled)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
