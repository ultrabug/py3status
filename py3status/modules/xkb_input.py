r"""
Switch inputs.

Configuration parameters:
    button_next: mouse button to cycle next layout (default 4)
    button_prev: mouse button to cycle previous layout (default 5)
    cache_timeout: refresh interval for this module; xkb-switch
        and swaymsg will listen for new updates instead (default 10)
    format: display format for this module (default '{format_input}')
    format_input: display format for inputs
        (default '[{alias}][\?soft  ][\?color=s {s}[ {v}]]')
    format_input_separator: show separator if more than one (default ' ')
    inputs: specify a list of inputs to use in swaymsg (default [])
    switcher: specify xkb-switch, xkblayout-state, xkbgroup,
        or swaymsg to use, otherwise auto (default None)
    thresholds: specify color thresholds to use
        *(default [("fr", "lightgreen"), ("ru", "lightcoral"),
        ("ua", "khaki"),  ("us", "lightskyblue")])*

Format placeholders:
    {format_input} format for inputs
    {input}        number of inputs, eg 1
    {switcher}     eg, xkb-switch, xkblayout-state, xkbgroup, swaymsg

format_input placeholders:
    xkb-switch:
    xkblayout-state:
    xkbgroup:
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
        {send_events}             eg, True
        {accel_speed}             eg, 0.0
        {accel_profile}           eg, adaptive
        {natural_scroll}          eg, adaptive
        {left_handed}             eg, False
        {middle_emulation}        eg, False
        {scroll_method}           eg, None
        {scroll_button}           eg, 274

        Use `swaymsg -r -t get_inputs` to get a list of current sway inputs
        and for a list of placeholders. Not all of placeholders will be usable.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    xkb-switch: program that allows to query and change the xkb layout state
    xkblayout-state: a command-line program to get/set the current keyboard layout
    xkbgroup: query and change xkb layout state
    swaymsg: send messages to sway window manager

Examples:
```
# sway users: for best results, add switcher to avoid false positives with `pgrep i3`
# because sway users can be using scripts, tools, et cetera with `i3` in its name.
xkb_input {
    switcher = "swaymsg"
}

# sway users: specify inputs to fnmatch
xkb_input {
    # display logitech identifiers
    inputs = [{"identifier": "*Logitech*"}]

    # display logi* keyboards only
    inputs = [{"name": "Logi*", "type": "keyb*"}]

    # display pointers only
    inputs = [{"type": "pointer"}]
}

# sway users: display inputs, optional aliases, et cetera
xkb_input {
    inputs = [
        {"identifier": "1625:3192:Heng_Yu_Technology_Poker_II", "alias": "Poker 2"},
        {"identifier": "0012:021:USB-HID_Keyboard", "alias": "Race 3"},
        {"identifier": "0123:45678:Logitech_MX_Ergo", "alias": "MX Ergo", "type": "pointer"},
    ]
}

# i3 users: display inputs - see https://wiki.archlinux.org/index.php/X_keyboard_extension
# $ setxkbmap -layout "us,fr,ru"  # install xkb-group to enable a listener thread
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

from pathlib import Path

STRING_ERROR = "invalid command `{}`"
STRING_NOT_AVAILABLE = "no available binary"
STRING_NOT_INSTALLED = "command `{}` not installed"


class Listener:
    """
    swaymsg -m - monitor for responses until killed
    xkb-switch -W - infinitely waits for group change
    """

    def __init__(self, parent):
        self.parent = parent
        if self.parent.switcher == "swaymsg":
            self.listen_command = ["swaymsg", "-m", "-t", "subscribe", "['input']"]
        elif self.parent.py3.check_commands("xkb-switch"):
            self.listen_command = ["xkb-switch", "-W"]
        else:
            return

        self.setup(parent)

    def setup(self, parent):
        from threading import Thread

        self.parent.cache_timeout = self.parent.py3.CACHE_FOREVER
        self.process = None

        t = Thread(target=self.start)
        t.daemon = True
        t.start()

    def start(self):
        from subprocess import Popen, PIPE

        try:
            self.process = Popen(self.listen_command, stdout=PIPE)
            while True:
                self.process.stdout.readline()
                code = self.process.poll()
                if code is not None:
                    msg = "Command `{}` terminated with returncode {}"
                    raise Exception(msg.format(" ".join(self.listen_command), code))
                self.parent.py3.update()
        except Exception as err:
            self.parent.error = err
            self.parent.py3.update()
        finally:
            self.kill()

    def kill(self):
        try:
            self.process.kill()
        except AttributeError:
            pass


class Xkb:
    """
    """

    def __init__(self, parent):
        self.parent = parent
        self.post_config_setup(parent)
        self.setup(parent)

    def py3_command_output(self, *args):
        try:
            return self.parent.py3.command_output(*args)
        except self.parent.py3.CommandError as err:
            self.parent.error = err
            raise err

    def py3_command_run(self, *args):
        try:
            return self.parent.py3.command_run(*args)
        except self.parent.py3.CommandError as err:
            self.parent.error = err
            raise err

    def post_config_setup(self, parent):
        self.name_mapping = {}
        self.reverse_name_mapping = {}
        self.variant_mapping = []

        try:
            with Path("/usr/share/X11/xkb/rules/base.lst").open() as f:
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
        except OSError as err:
            self.parent.error = err

    def setup(self, parent):
        pass

    def add_libinput(self, _input):
        pass

    def set_xkb_layout(self, delta):
        pass


class Xkbgroup(Xkb):
    """
    xkbgroup - query and change xkb layout state
    """

    def setup(self, parent):
        from xkbgroup import XKeyboard

        self.xo = XKeyboard
        self.map = {"num": "c", "name": "n", "symbol": "s", "variant": "v"}

    def get_xkb_inputs(self):
        xo = self.xo()
        group_data = xo.group_data._asdict()
        xkb_input = {self.map[k]: v for k, v in group_data.items()}
        xkb_input["e"] = xkb_input["v"] or xkb_input["s"]
        xkb_input["C"] = xo.groups_count

        return [xkb_input]

    def set_xkb_layout(self, delta):
        xo = self.xo()
        xo.group_num = (xo.group_num + delta) % xo.groups_count


class Xkb_Switch(Xkb):
    """
    xkb-switch - program that allows to query and change the xkb layout state
    """

    def setup(self, parent):
        self.init_cC = self.parent.py3.format_contains(self.parent.format_input, "[cC]")

    def get_xkb_inputs(self):
        s = output = self.py3_command_output("xkb-switch -p").strip()
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

        xkb_input = {"s": s, "v": v, "e": v or s, "n": n}

        if self.init_cC:
            layouts = self.py3_command_output("xkb-switch -l").splitlines()
            xkb_input["C"] = len(layouts)

            for index, layout in enumerate(layouts):
                if layout == output:
                    xkb_input["c"] = index
                    break

        return [xkb_input]

    def set_xkb_layout(self, delta):
        if delta > 0:
            self.py3_command_run("xkb-switch -n")
        else:
            i = self.py3_command_output("xkb-switch -p").strip()
            s = self.py3_command_output("xkb-switch -l").splitlines()
            self.py3_command_run("xkb-switch -s {}".format(s[s.index(i) - 1]))


class Xkblayout_State(Xkb):
    """
    xkblayout-state - a command-line program to get/set the current keyboard layout
    """

    def setup(self, parent):
        self.placeholders = list("cnsveC")
        self.separator = "|SEPARATOR|"
        self.xkblayout_command = "xkblayout-state print {}".format(
            self.separator.join("%" + x for x in self.placeholders)
        )

    def get_xkb_inputs(self):
        line = self.py3_command_output(self.xkblayout_command)
        xkb_input = dict(zip(self.placeholders, line.split(self.separator)))
        xkb_input["n"] = self.name_mapping.get(xkb_input["s"], xkb_input["n"])

        return [xkb_input]

    def set_xkb_layout(self, delta):
        self.py3_command_run(
            "xkblayout-state set {}{}".format({+1: "+", -1: "-"}[delta], abs(delta))
        )


class Swaymsg(Xkb):
    """
    swaymsg - send messages to sway window manager
    """

    def setup(self, parent):
        from json import loads
        from fnmatch import fnmatch

        self.excluded = ["alias"]
        self.fnmatch, self.loads = (fnmatch, loads)
        self.map = {"enabled": True, "disabled": False, "none": None}
        self.swaymsg_command = ["swaymsg", "--raw", "--type", "get_inputs"]

    def add_libinput(self, _input):
        libinput = _input.pop("libinput", {})
        _input.update({k: self.map.get(v, v) for k, v in libinput.items()})

        return _input

    def update_xkb_input(self, xkb_input, _filter):
        xkb_input["alias"] = _filter.get("alias", xkb_input["name"])

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

    def get_xkb_inputs(self):
        try:
            xkb_data = self.loads(self.py3_command_output(self.swaymsg_command))
        except Exception:
            xkb_data = []

        new_input = []
        for xkb_input in xkb_data:
            if self.parent.inputs:
                for _filter in self.parent.inputs:
                    for key, value in _filter.items():
                        if key in self.excluded or key not in xkb_input:
                            continue
                        if not self.fnmatch(xkb_input[key], value):
                            break
                    else:
                        new_input.append(self.update_xkb_input(xkb_input, _filter))
            else:
                _filter = {}
                new_input.append(self.update_xkb_input(xkb_input, _filter))

        return new_input


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_prev = 5
    cache_timeout = 10
    format = "{format_input}"
    format_input = r"[{alias}][\?soft  ][\?color=s {s}[ {v}]]"
    format_input_separator = " "
    inputs = []
    switcher = None
    thresholds = [
        ("fr", "lightgreen"),
        ("ru", "lightcoral"),
        ("ua", "khaki"),
        ("us", "lightskyblue"),
    ]

    def post_config_hook(self):
        switchers = ["xkb-switch", "xkblayout-state", "xkbgroup", "swaymsg"]
        if not self.switcher:
            if self.py3.get_wm_msg() == "swaymsg":
                self.switcher = "swaymsg"
            else:
                self.switcher = self.py3.check_commands(switchers)
        elif self.switcher not in switchers:
            raise Exception(STRING_ERROR.format(self.switcher))
        elif not self.py3.check_commands(self.switcher):
            raise Exception(STRING_NOT_INSTALLED.format(self.switcher))
        if not self.switcher:
            raise Exception(STRING_NOT_AVAILABLE)

        self.error = None
        self.input_backend = globals()[self.switcher.replace("-", "_").title()](self)
        if getattr(self, "listener", True):
            self.listener_backend = Listener(self)

        self.thresholds_init = {}
        for name in ["format", "format_input"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def _stop_on_errors(self):
        if self.error:
            self.kill()
            self.py3.error(str(self.error), self.py3.CACHE_FOREVER)

    def xkb_input(self):
        xkb_inputs = self.input_backend.get_xkb_inputs()
        self._stop_on_errors()
        new_input = []

        for _input in xkb_inputs:
            _input = self.input_backend.add_libinput(_input) or _input
            for x in self.thresholds_init["format_input"]:
                if x in _input:
                    self.py3.threshold_get_color(_input[x], x)
            new_input.append(self.py3.safe_format(self.format_input, _input))

        format_input_separator = self.py3.safe_format(self.format_input_separator)
        format_input = self.py3.composite_join(format_input_separator, new_input)

        input_data = {
            "format_input": format_input,
            "input": len(xkb_inputs),
            "switcher": self.switcher,
        }

        for x in self.thresholds_init["format"]:
            if x in input_data:
                self.py3.threshold_get_color(input_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, input_data),
        }

    def kill(self):
        try:
            self.listener_backend.kill()
        except AttributeError:
            pass

    def on_click(self, event):
        button = event["button"]
        if button == self.button_next:
            self.input_backend.set_xkb_layout(+1)
        elif button == self.button_prev:
            self.input_backend.set_xkb_layout(-1)


if __name__ == "__main__":

    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
