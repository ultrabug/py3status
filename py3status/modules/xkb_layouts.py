# -*- coding: utf-8 -*-
"""
Switch keyboard layouts.

Configuration parameters:
    button_next: mouse button to cycle next layout (default 4)
    button_prev: mouse button to cycle previous layout (default 5)
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default "[\?color=s {s}][ {v}]")
    thresholds: specify color thresholds to use
        *(default [("fr", "#268BD2"), ("ru", "#F75252"),
        ("ua", "#FCE94F"), ("us", "#729FCF")])*

Format placeholders:
    xkblayout-state:
        {c} layout number, eg 0
        {n} layout name, eg English
        {s} layout symbol, eg us
        {v} layout variant, eg basic
        {e} layout variant, {v} or {s}, eg dvorak
        {C} layout count, eg 2
    xkbgroup:
        {c} layout number, eg 0
        {n} layout name, eg English (US)
        {s} layout symbol, eg us
        {v} layout variant, eg basic
        {e} layout variant, {v} or {s}, eg dvorak
        {C} layout count, eg 2
    xkb-switch:
        {s} layout symbol, eg us
        {e} layout variant, compatibility alias to {s}, eg us
        {C} layout count, eg 2

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    xkblayout-state: a small command-line program to get/set the current keyboard layout
    xkbgroup: query and change xkb layout state
    xkb-switch: program that allows to query and change the xkb layout state

@author lasers, saengowp

SAMPLE OUTPUT
[{"full_text": "Xkb "}, {"color": "#00FFFF", "full_text": "us"}]

ru
[{"full_text": "Xkb "}, {"color": "#00FFFF", "full_text": "ru"}]
"""

STRING_ERROR = "invalid command `%s`"
STRING_NOT_AVAILABLE = "no available binary"
COMMAND_NOT_INSTALLED = "command `%s` not installed"


class Xkb:
    def __init__(self, parent):
        self.parent = parent
        self.setup(parent)

    def setup(self, parent):
        pass


class Xkbgroup(Xkb):
    def setup(self, parent):
        from xkbgroup import XKeyboard

        self.xo = XKeyboard
        self.active_index = self.xo().group_num
        self.map = {"num": "c", "name": "n", "symbol": "s", "variant": "v"}

    def get_xkb_data(self):
        xo = self.xo()
        group_data = xo.group_data._asdict()
        data = {self.map[k]: v for k, v in group_data.items()}
        data["e"] = data["v"] or data["s"]
        data["C"] = xo.groups_count
        return data

    def set_xkb_layout(self, delta):
        xo = self.xo()
        self.active_index += delta
        self.active_index %= xo.groups_count
        xo.group_num = self.active_index + 1


class Xkb_Switch(Xkb):
    def setup(self, parent):
        self.placeholders = self.parent.py3.get_placeholders_list(
            self.parent.format, "[seC]"
        )

    def get_xkb_data(self):
        data = {}
        used = None
        for key in self.placeholders:
            if key in ["s", "e"]:
                if used:
                    value = used
                else:
                    value = self.parent.py3.command_output("xkb-switch -p").strip()
                    used = value
            elif key == "C":
                output = self.parent.py3.command_output("xkb-switch -l")
                value = len(output.splitlines())
            data[key] = value
        return data

    def set_xkb_layout(self, delta):
        if delta > 0:
            self.parent.py3.command_run("xkb-switch -n")
        else:
            i = self.parent.py3.command_output("xkb-switch -p").strip()
            s = self.parent.py3.command_output("xkb-switch -l").splitlines()
            self.parent.py3.command_run("xkb-switch -s {}".format(s[s.index(i) - 1]))


class Xkblayout_State(Xkb):
    def setup(self, parent):
        self.placeholders = self.parent.py3.get_placeholders_list(
            self.parent.format, "[cnsveC]"
        )
        self.separator = "|SEPARATOR|"
        self.xkblayout_command = "xkblayout-state print {}".format(
            self.separator.join(["%" + x for x in self.placeholders])
        )

    def get_xkb_data(self):
        line = self.parent.py3.command_output(self.xkblayout_command)
        return dict(zip(self.placeholders, line.split(self.separator)))

    def set_xkb_layout(self, delta):
        self.parent.py3.command_run(
            "xkblayout-state set {}{}".format({+1: "+", -1: "-"}[delta], abs(delta))
        )


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_prev = 5
    cache_timeout = 10
    format = "[\?color=s {s}][ {v}]"
    thresholds = [
        ("fr", "#268BD2"),
        ("ru", "#F75252"),
        ("ua", "#FCE94F"),
        ("us", "#729FCF"),
    ]

    def post_config_hook(self):
        # specify xkblayout-state, xkbgroup, or xkb-switch to use, otherwise auto
        self.command = getattr(self, "command", None)

        keyboard_commands = ["xkblayout-state", "xkbgroup", "xkb-switch"]
        if not self.command:
            self.command = self.py3.check_commands(keyboard_commands)
        elif self.command not in keyboard_commands:
            raise Exception(STRING_ERROR % self.command)
        elif not self.py3.check_commands(self.command):
            raise Exception(COMMAND_NOT_INSTALLED % self.command)
        if not self.command:
            raise Exception(
                "%s (%s)" % (STRING_NOT_AVAILABLE, " or ".join(keyboard_commands))
            )

        self.backend = globals()[self.command.replace("-", "_").title()](self)
        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def xkb_layouts(self):
        xkb_data = self.backend.get_xkb_data()

        for x in self.thresholds_init:
            if x in xkb_data:
                self.py3.threshold_get_color(xkb_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, xkb_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_next:
            self.backend.set_xkb_layout(+1)
        elif button == self.button_prev:
            self.backend.set_xkb_layout(-1)


if __name__ == "__main__":

    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
