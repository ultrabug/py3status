# -*- coding: utf-8 -*-
"""
Switch inputs.

Configuration parameters:
    button_next: mouse button to cycle next layout (default 4)
    button_prev: mouse button to cycle previous layout (default 5)
    cache_timeout: refresh interval for i3 switchers (default 10)
    format: display format for this module (default '{format_input}')
    format_input: display format for inputs
        (default '[{alias}][\?soft  ][\?color=s {s}[ {v}]]')
    format_input_separator: show separator if more than one (default ' ')
    format_libinput: display format for libinputs (default None)
    inputs: specify a list of inputs to use (default [])
    switcher: specify xkblayout-state, xkbgroup, xkb-switch,
        or swaymsg to use, otherwise auto (default None)
    thresholds: specify color thresholds to use
        *(default [("fr", "lightgreen"), ("ru", "lightcoral"),
        ("ua", "khaki"),  ("us", "lightskyblue")])*

Format placeholders:
    {format_input} format for inputs
    {input}        number of inputs, eg 1
    {switcher}     eg, xkblayout-state, xkbgroup, xkb-switch, swaymsg

format_input placeholders:
    xkblayout-state:
    xkbgroup:
    xkb-switch:
    swaymsg:
        {c} layout number, eg, 0
        {n} layout name, eg, English (US)
        {s} layout symbol, eg, us
        {v} layout variant, eg, basic
        {e} layout variant, {v} or {s}, eg, dvorak
        {C} layout count, eg, 2
    swaymsg:
        {alias}                   custom string or {name}
        {identifier}              eg, 162:253 USB-HID Keyboard
        {name}                    eg, Trackball, Keyboard, etc
        {vendor}                  eg, 320
        {product}                 eg, 556
        {type}                    eg, pointer, keyboard, touchpad, etc
        {xkb_layout_names}        eg, English (US), French, Russian
        {xkb_active_layout_index} eg, 0, 1, 2, etc
        {xkb_active_layout_name}  eg, English (US)
        {format_libinput}         format for libinputs

format_libinput placeholders:
    {send_events}      eg, enabled
    {accel_speed}      eg, 0.0
    {accel_profile}    eg, adaptive
    {natural_scroll}   eg, adaptive
    {left_handed}      eg, disabled
    {middle_emulation} eg, disabled
    {scroll_method}    eg, none
    {scroll_button}    eg, 274

    Use `swaymsg -r -t get_inputs` to get a list of current sway inputs
    and for a list of placeholders. Not all of placeholders will be usable.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    xkblayout-state: a command-line program to get/set the current keyboard layout
    xkbgroup: query and change xkb layout state
    xkb-switch: program that allows to query and change the xkb layout state
    swaymsg: send messages to sway window manager

Examples:
```
# sway users: for best results, add switcher to avoid false positives with `pgrep i3`
# because sway users can be using scripts, tools, et cetera with `i3` in its name.
xkb_input {
    switcher = "swaymsg"
}

# sway users: add inputs, aliases, icons, et cetera
xkb_input {
    inputs = [
        {"identifier": "1625:3192:Heng_Yu_Technology_Poker_II","alias": "⌨ Poker 2"},
        {"identifier": "0012:021:USB-HID_Keyboard", "alias": "⌨ Race 3"},
        {"identifier": "0123:45678:Logitech_MX_Ergo", "alias": "🖲️ MX Ergo", "type": "pointer"},
    ]
}

# sway users: specify input keys to fnmatch
xkb_input {
    # display logitech identifiers
    inputs = [{"identifier": "*Logitech*"}]

    # display logi* keyboards only
    inputs = [{"name": "Logi*", "type": "key*"}]

    # display pointers only
    inputs = [{"type": "pointer"}]
}

# i3 users: add inputs - see https://wiki.archlinux.org/index.php/X_keyboard_extension
# setxkbmap -layout "us,fr,ru"
```

@author lasers, saengowp, javiertury

SAMPLE OUTPUT
{"color": "#87CEFA", "full_text": "us"}

fr
{"color": "#90EE90", "full_text": "fr"}

ru
{"color": "#F08080", "full_text": "ru"}

au
{"color": "#F0E68C", "full_text": "au"}
"""

STRING_ERROR = "invalid command `%s`"
STRING_NOT_AVAILABLE = "no available binary"
COMMAND_NOT_INSTALLED = "command `%s` not installed"


class Xkb:
    """
    """

    def __init__(self, parent):
        self.parent = parent
        self.post_config_setup(parent)
        self.setup(parent)

    def post_config_setup(self, parent):
        self.name_mapping = {}
        self.reverse_name_mapping = {}
        self.variant_mapping = []

        try:
            with open("/usr/share/X11/xkb/rules/base.lst") as f:
                for chunk in f.read().split("\n\n"):
                    if "! layout" in chunk:
                        for line in chunk.splitlines()[1:]:
                            fields = line.split()
                            symbol, name = (fields[0], " ".join(fields[1:]))
                            self.name_mapping[symbol] = name
                            self.reverse_name_mapping[name] = (symbol, None)
                    if "! variant" in chunk:
                        for line in chunk.splitlines()[1:]:
                            fields = line.split()
                            variant, symbol, name = (
                                fields[0],
                                fields[1][:-1],
                                " ".join(fields[2:]),
                            )
                            self.reverse_name_mapping[name] = (symbol, variant)
                            self.variant_mapping.append((variant, symbol, name))
        except IOError:
            pass

    def setup(self, parent):
        pass

    def kill(self):
        pass

    def make_format_libinput(self, _input):
        pass

    def make_format_input(self, inputs):
        new_input = []
        for _input in inputs:
            _input = self.make_format_libinput(_input) or _input
            for x in self.parent.thresholds_init["format_input"]:
                if x in _input:
                    self.parent.py3.threshold_get_color(_input[x], x)
            new_input.append(
                self.parent.py3.safe_format(self.parent.format_input, _input)
            )

        format_input_separator = self.parent.py3.safe_format(
            self.parent.format_input_separator
        )
        format_input = self.parent.py3.composite_join(format_input_separator, new_input)

        return {
            "format_input": format_input,
            "input": len(inputs),
            "switcher": self.parent.switcher,
        }

    def set_xkb_layout(self, delta):
        pass


class Xkbgroup(Xkb):
    """
    xkbgroup - query and change xkb layout state
    """

    def setup(self, parent):
        from xkbgroup import XKeyboard

        self.xo = XKeyboard
        self.active_index = self.xo().group_num
        self.map = {"num": "c", "name": "n", "symbol": "s", "variant": "v"}

    def get_xkb_data(self):
        xo = self.xo()
        group_data = xo.group_data
        group_data = xo.group_data._asdict()
        temporary = {self.map[k]: v for k, v in group_data.items()}
        temporary["e"] = temporary["v"] or temporary["s"]
        temporary["C"] = xo.groups_count

        return self.make_format_input([temporary])

    def set_xkb_layout(self, delta):
        xo = self.xo()
        self.active_index += delta
        self.active_index %= xo.groups_count
        xo.group_num = self.active_index + 1


class Xkb_Switch(Xkb):
    """
    xkb-switch - program that allows to query and change the xkb layout state
    """

    def setup(self, parent):
        self.init_cC = self.parent.py3.format_contains(self.parent.format_input, "[cC]")

    def get_xkb_data(self):
        s = output = self.parent.py3.command_output("xkb-switch -p").strip()
        v = None

        if "(" in s and ")" in s:
            v = s[s.find("(") + 1 : s.find(")")]
            s = s[: s.find("(")]

        for variant, symbol, name in self.variant_mapping:
            if (v, s) == (variant, symbol):
                n = name
                break
        else:
            n = self.name_mapping.get(s)

        temporary = {"s": s, "v": v, "e": v or s, "n": n}

        if self.init_cC:
            layouts = self.parent.py3.command_output("xkb-switch -l").splitlines()
            temporary["C"] = len(layouts)

            for index, layout in enumerate(layouts):
                if layout == output:
                    temporary["c"] = index
                    break

        return self.make_format_input([temporary])

    def set_xkb_layout(self, delta):
        if delta > 0:
            self.parent.py3.command_run("xkb-switch -n")
        else:
            i = self.parent.py3.command_output("xkb-switch -p").strip()
            s = self.parent.py3.command_output("xkb-switch -l").splitlines()
            self.parent.py3.command_run("xkb-switch -s {}".format(s[s.index(i) - 1]))


class Xkblayout_State(Xkb):
    """
    xkblayout-state - a command-line program to get/set the current keyboard layout
    """

    def setup(self, parent):
        self.placeholders = list("cnsveC")
        self.separator = "|SEPARATOR|"
        self.xkblayout_command = "xkblayout-state print {}".format(
            self.separator.join(["%" + x for x in self.placeholders])
        )

    def get_xkb_data(self):
        line = self.parent.py3.command_output(self.xkblayout_command)
        temporary = dict(zip(self.placeholders, line.split(self.separator)))
        temporary["n"] = self.name_mapping.get(temporary["s"], temporary["n"])

        return self.make_format_input([temporary])

    def set_xkb_layout(self, delta):
        self.parent.py3.command_run(
            "xkblayout-state set {}{}".format({+1: "+", -1: "-"}[delta], abs(delta))
        )


class Swaymsg(Xkb):
    """
    swaymsg - send messages to sway window manager
    """

    def setup(self, parent):
        from json import loads
        from fnmatch import fnmatch
        from threading import Thread

        self.fnmatch, self.loads = (fnmatch, loads)
        self.swaymsg_command = ["swaymsg", "--raw", "--type", "get_inputs"]
        if self.parent.format_libinput and self.parent.py3.format_contains(
            self.parent.format_input, "format_libinput"
        ):
            self.make_format_libinput = self.__make_format_libinput

        self.parent.cache_timeout = self.parent.py3.CACHE_FOREVER
        self.process = None

        t = Thread(target=self.start)
        t.daemon = True
        t.start()

    def start(self):
        from subprocess import Popen, PIPE

        swaymsg_command = ["swaymsg", "--monitor", "--type", "subscribe", "['input']"]

        try:
            self.process = Popen(swaymsg_command, stdout=PIPE)
            while True:
                self.process.stdout.readline()
                if self.process.poll() is not None:
                    raise Exception
                self.parent.py3.update()
        except Exception as err:
            self.parent.error = err
        finally:
            self.parent.py3.update()
            self.kill()

    def kill(self):
        self.process.kill()

    def __make_format_libinput(self, _input):
        libinput = _input.pop("libinput", {})
        for x in self.parent.thresholds_init["format_libinput"]:
            if x in libinput:
                self.parent.py3.threshold_get_color(libinput[x], x)

        format_libinput = self.parent.py3.safe_format(
            self.parent.format_libinput, libinput
        )
        _input["format_libinput"] = format_libinput

        return _input

    def update_xkb_input(self, xkb_input, user_input):
        xkb_input["alias"] = user_input.get("alias", xkb_input["name"])

        if "xkb_active_layout_name" in xkb_input:
            c = xkb_input["xkb_active_layout_index"]
            C = len(xkb_input["xkb_layout_names"])
            n = xkb_input["xkb_active_layout_name"]
            s, v = self.reverse_name_mapping.get(n, (None, None))

            if s is None and "(" in n and ")" in n:
                s = n[n.find("(") + 1 : n.find(")")].lower()
                n = n[: n.find("(") - 1]

            xkb_input["xkb_layout_names"] = ", ".join(xkb_input["xkb_layout_names"])
            xkb_input.update({"c": c, "C": C, "s": s, "e": v or s, "n": n, "v": v})

        return xkb_input

    def get_xkb_data(self):
        try:
            xkb_data = self.loads(self.parent.py3.command_output(self.swaymsg_command))
        except Exception as err:
            self.parent.error = err
            xkb_data = []

        excluded = ["alias"]
        new_xkb = []

        for xkb_input in xkb_data:
            if self.parent.inputs:
                for _filter in self.parent.inputs:
                    for key, value in _filter.items():
                        if key in excluded or key not in xkb_input:
                            continue
                        if not self.fnmatch(xkb_input[key], value):
                            break
                    else:
                        new_xkb.append(self.update_xkb_input(xkb_input, _filter))
            else:
                _filter = {}
                new_xkb.append(self.update_xkb_input(xkb_input, _filter))

        return self.make_format_input(new_xkb)


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_prev = 5
    cache_timeout = 10
    format = "{format_input}"
    format_input = "[{alias}][\?soft  ][\?color=s {s}[ {v}]]"
    format_input_separator = " "
    format_libinput = None
    inputs = []
    switcher = None
    thresholds = [
        ("fr", "lightgreen"),
        ("ru", "lightcoral"),
        ("ua", "khaki"),
        ("us", "lightskyblue"),
    ]

    def post_config_hook(self):
        switchers = ["xkblayout-state", "xkbgroup", "xkb-switch", "swaymsg"]
        if not self.switcher:
            if self.py3.get_wm_msg() == "swaymsg":
                self.switcher = "swaymsg"
            else:
                self.switcher = self.py3.check_commands(switchers)
        elif self.switcher not in switchers:
            raise Exception(STRING_ERROR % self.switcher)
        elif not self.py3.check_commands(self.switcher):
            raise Exception(COMMAND_NOT_INSTALLED % self.switcher)

        self.error = None
        self.backend = globals()[self.switcher.replace("-", "_").title()](self)

        self.thresholds_init = {}
        for name in ["format", "format_input", "format_libinput"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def xkb_input(self):
        if self.error:
            self.backend.kill()
            self.py3.error(str(self.error), self.py3.CACHE_FOREVER)

        xkb_data = self.backend.get_xkb_data()

        for x in self.thresholds_init["format"]:
            if x in xkb_data:
                self.py3.threshold_get_color(xkb_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, xkb_data),
        }

    def kill(self):
        self.backend.kill()

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
