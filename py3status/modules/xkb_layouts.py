# -*- coding: utf-8 -*-
"""
Switch keyboard layouts.

Configuration parameters:
    button_next: mouse button to cycle next layout (default 4)
    button_prev: mouse button to cycle previous layout (default 5)
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_input}')
    format_input: display format for inputs, otherwise auto (default None)
    format_input_separator: show separator if more than one (default ' ')
    inputs: specify a list of inputs to use (default [])
    thresholds: specify color thresholds to use
        *(default [("fr", "#268BD2"), ("ru", "#F75252"),
        ("ua", "#FCE94F"), ("us", "#729FCF")])*

Format placeholders:
    {format_input} format for inputs

format_input placeholders:
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
    swaymsg:
        {identifier} eg 162:253 USB-HID Keyboard
        {name} eg Trackball, Keyboard, etc
        {vendor}  eg 320
        {product} eg 556
        {type} eg pointer, keyboard, touchpad
        {xkb_layout_names} eg English (US)
        {xkb_active_layout_index} eg 0
        {format_libinput} format for libinputs

format_libinput placeholders:
    {send_event}
    {accel_speed}
    {natural_scroll}
    {left_handed}
    {middle_emulation}
    {scroll_method}
    {scroll_button}

    Use `swaymsg -r -t get_inputs` for a list of placeholders from
    current sway inputs. Not all of placeholders will be usable.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    xkblayout-state: a small command-line program to get/set the current keyboard layout
    xkbgroup: query and change xkb layout state
    xkb-switch: program that allows to query and change the xkb layout state
    swaymsg: send messages to a running instance of sway over the ipc socket

@author lasers, saengowp, javiertury

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
        if self.format_input is None:
            self.format_input = "[\?color=s {s}][ {v}]"
        self.parent.thresholds_init = {
            "format": self.parent.py3.get_color_names_list(self.parent.format)
        }


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


class Swaymsg(Xkb):
    def setup(self, parent):
        from json import loads
        from fnmatch import fnmatch

        self.loads = loads
        self.fnmatch = fnmatch

        self.swaymsg_command = "swaymsg --raw --type get_inputs".split()

        if self.parent.format is None:
            self.parent.format = "{format_input}"
        if self.parent.format_input is None:
            self.parent.format_input = "{name}"

        self.parent.thresholds_init = {
            "format": self.parent.py3.get_color_names_list(self.parent.format),
            "format_input": self.parent.py3.get_color_names_list(
                self.parent.format_input
            ),
        }

    def get_xkb_data(self):
        xkb_data = self.loads(self.parent.py3.command_output(self.swaymsg_command))

        new_input = []
        for xkb_input in xkb_data:
            skip = False
            for filtered_input in self.parent.inputs:
                skip = True
                for k, v in filtered_input.items():
                    xk = xkb_input.get(k, "")
                    xv = xkb_input.get(v, "")
                    self.parent.py3.log("KEY: {} vs {}".format(k, xk))
                    self.parent.py3.log("VALUE: {} vs {}".format(v, xv))
                    self.parent.py3.log("-" * 5)
                    self.parent.py3.log("=" * 10)
                    if self.fnmatch(xv, v):
                        skip = False
                # value = xkb_input.get(v)
                # self.parent.py3.log(value)
                # self.parent.py3.log(v)
                # if self.fnmatch(value, v):
                #     skip = False
            if skip:
                self.parent.py3.log("xxxxxxxxxxxx skipping")
                continue

                for x in self.parent.thresholds_init["format_input"]:
                    if x in xkb_input:
                        self.parent.py3.threshold_get_color(xkb_input[x], x)

                new_input.append(
                    self.parent.py3.safe_format(self.parent.format_input, xkb_input)
                )

        format_input_separator = self.parent.py3.safe_format(
            self.parent.format_input_separator
        )
        format_input = self.parent.py3.composite_join(format_input_separator, new_input)

        return {"format_input": format_input}

    def set_xkb_layout(self, delta):
        pass


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_prev = 5
    cache_timeout = 10
    format = "{format_input}"
    format_input = None
    format_input_separator = " "
    inputs = []
    thresholds = [
        ("fr", "#268BD2"),
        ("ru", "#F75252"),
        ("ua", "#FCE94F"),
        ("us", "#729FCF"),
    ]

    # inputs = [{"type": "keyboard", "name": "*pple*"}]

    def post_config_hook(self):
        # specify xkblayout-state, xkbgroup, xkb-switch, or swaymsg to use, otherwise auto
        self.command = getattr(self, "command", None)

        keyboard_commands = ["xkblayout-state", "xkbgroup", "xkb-switch", "swaymsg"]
        if not self.command:
            self.command = self.py3.check_commands(keyboard_commands)
        elif self.command not in keyboard_commands:
            raise Exception(STRING_ERROR % self.command)
        elif not self.py3.check_commands(self.command):
            raise Exception(COMMAND_NOT_INSTALLED % self.command)

        try:
            self.backend = globals()[self.command.replace("-", "_").title()](self)
            self.backend.get_xkb_data()
        except Exception:
            raise Exception(
                "%s (%s)" % (STRING_NOT_AVAILABLE, " or ".join(keyboard_commands))
            )

    def xkb_layouts(self):
        xkb_data = self.backend.get_xkb_data()

        for x in self.thresholds_init["format"]:
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
