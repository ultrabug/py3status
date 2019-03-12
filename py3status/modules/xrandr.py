# -*- coding: utf-8 -*-
"""
Control screen layout.

This modules allows you to handle your screens outputs directly from your bar!
    - Detect and propose every possible screen combinations
    - Switch between combinations using click events and mouse scroll
    - Activate the screen or screen combination on a single click
    - It will detect any newly connected or removed screen automatically

For convenience, this module also proposes some added features:
    - Dynamic parameters for POSITION and WORKSPACES assignment (see below)
    - Automatic fallback to a given screen or screen combination when no more
        screen is available (handy for laptops)
    - Automatically apply this screen combination on start: no need for xorg!
    - Automatically move workspaces to screens when they are available
    - Define your own subset of output combinations to use

Configuration parameters:
    cache_timeout: how often to (re)detect the outputs (default 10)
    command: a custom command to be run after display configuration changes
        (default None)
    fallback: when the current output layout is not available anymore,
        fallback to this layout if available. This is very handy if you
        have a laptop and switched to an external screen for presentation
        and want to automatically fallback to your laptop screen when you
        disconnect the external screen. (default True)
    fixed_width: show output as fixed width (default True)
    force_on_change: switch display layout to the leftmost combination mode
        of the given list whenever it is available. The combination modes are
        checked from left (high priority) to right (less priority) until
        one matches.
        Example:
            We have a laptop with internal screen and we are often moving from
            our desk where another screen is available. We want the layout to
            follow our changes so that we do not have to switch manually.
            So whenever we plug at our desk, we want the second monitor to be
            used, and whenever we go away we want everything back on the laptop
            screen automatically:
            ```
            force_on_change = ["eDP1+DP1", "eDP1"]
            ```
        NOTES:
            Click controls will override `force_on_change` until the layout
            changes in the background so you can still manually control your
            layout changes on the bar.
            Use the `force_on_start` to handle initial layout setup on module
            startup along with this feature to benefit from fully dynamic and
            automated changes of screen layouts.
        (default [])
    force_on_start: switch to the given combination mode if available
        when the module starts (saves you from having to configure xorg)
        (default None)
    format: display format for xrandr
        (default '{output}')
    hide_if_single_combination: hide if only one combination is available
        (default False)
    icon_clone: icon used to display a 'clone' combination
        (default '=')
    icon_extend: icon used to display a 'extend' combination
        (default '+')
    on_udev_drm: dynamic variable to watch for `drm` udev subsystem events to
        trigger specified action.
        (default 'refresh_and_freeze')
    output_combinations: string used to define your own subset of output
        combinations to use, instead of generating every possible combination
        automatically. Provide the values in the format that this module uses,
        splitting the combinations using '|' character.
        The combinations will be rotated in the exact order as you listed them.
        When an output layout is not available any more, the configurations
        are automatically filtered out.
        Example:
            Assuming the default values for `icon_clone` and `icon_extend`
            are used, and assuming you have two screens 'eDP1' and 'DP1', the
            following setup will reduce the number of output combinations
            from four (every possible one) down to two.
            ```
            output_combinations = "eDP1|eDP1+DP1"
            ```
        (default None)

Dynamic configuration parameters:
    <OUTPUT>_pos: apply the given position to the OUTPUT
        Example: DP1_pos = "-2560x0"
        Example: DP1_pos = "above eDP1"
        Example: DP1_pos = "below eDP1"
        Example: DP1_pos = "left-of LVDS1"
        Example: DP1_pos = "right-of eDP1"
    <OUTPUT>_workspaces: comma separated list of workspaces to move to
        the given OUTPUT when it is activated
        Example: DP1_workspaces = "1,2,3"
    <OUTPUT>_rotate: rotate the output as told
        Example: DP1_rotate = "left"
    <OUTPUT>_mode: define the mode (resolution) for the output
                   if not specified use --auto : prefered mode
        Example: eDP1_mode = "2560x1440
    <OUTPUT>_primary: apply the primary to the OUTPUT
        Example: DP1_primary = True

Format placeholders:
    {output} xrandr output

Color options:
    color_bad: Displayed layout unavailable
    color_degraded: Using a fallback layout
    color_good: Displayed layout active

Notes:
    Some days are just bad days. Running `xrandr --query` command can
    cause unexplainable brief screen freezes due to an overall combination
    of computer hardware, installed software, your choice of linux distribution,
    and/or some other unknown factors such as recent system updates.

    Configuring `cache_timeout` with a different number, eg `3600` (an hour)
    or `-1` (runs once) can be used to remedy this issue. See issue #580.

Examples:
```
# start with a preferable setup
xrandr {
    force_on_start = "eDP1+DP1"
    DP1_pos = "left-of eDP1"
    VGA_workspaces = "7"
}
```

@author ultrabug

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'LVDS1+DP1'}

mirror
{'full_text': 'LVDS1=DP1'}

single_1
{'full_text': u'LVDS1'}

single_2
{'full_text': 'DP1'}
"""

from collections import deque
from collections import OrderedDict
from itertools import combinations
from time import sleep


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    command = None
    fallback = True
    fixed_width = True
    force_on_change = []
    force_on_start = None
    format = "{output}"
    hide_if_single_combination = False
    icon_clone = "="
    icon_extend = "+"
    on_udev_drm = "refresh_and_freeze"
    output_combinations = None

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "format_clone",
                    "new": "icon_clone",
                    "msg": "obsolete parameter use `icon_clone`",
                },
                {
                    "param": "format_extend",
                    "new": "icon_extend",
                    "msg": "obsolete parameter use `icon_extend`",
                },
            ]
        }

    def post_config_hook(self):
        """
        Initialization
        """
        self._no_force_on_change = True
        self.active_comb = None
        self.active_layout = None
        self.active_mode = "extend"
        self.displayed = None
        self.max_width = 0

    def _get_layout(self):
        """
        Get the outputs layout from xrandr and try to detect the
        currently active layout as best as we can on start.
        """
        connected = list()
        active_layout = list()
        disconnected = list()
        layout = OrderedDict(
            {"connected": OrderedDict(), "disconnected": OrderedDict()}
        )

        current = self.py3.command_output("xrandr")
        for line in current.splitlines():
            try:
                s = line.split(" ")
                infos = line[line.find("(") :]
                if s[1] == "connected":
                    output, state, mode = s[0], s[1], None
                    for index, x in enumerate(s[2:], 2):
                        if "x" in x and "+" in x:
                            mode = x
                            active_layout.append(output)
                            infos = line[line.find(s[index + 1]) :]
                            break
                        elif "(" in x:
                            break
                    connected.append(output)
                elif s[1] == "disconnected":
                    output, state, mode = s[0], s[1], None
                    disconnected.append(output)
                else:
                    continue
            except Exception as err:
                self.py3.log('xrandr error="{}"'.format(err))
            else:
                layout[state][output] = {"infos": infos, "mode": mode, "state": state}

        # initialize the active layout
        if self.active_layout is None:
            self.active_comb = tuple(active_layout)
            self.active_layout = self._get_string_and_set_width(
                tuple(active_layout), self.active_mode
            )

        return layout

    def _set_available_combinations(self):
        """
        Generate all connected outputs combinations and
        set the max display width while iterating.
        """
        available = set()
        combinations_map = {}

        whitelist = None
        if self.output_combinations:
            whitelist = self.output_combinations.split("|")

        self.max_width = 0
        for output in range(len(self.layout["connected"])):
            for comb in combinations(self.layout["connected"], output + 1):
                for mode in ["clone", "extend"]:
                    string = self._get_string_and_set_width(comb, mode)
                    if whitelist and string not in whitelist:
                        continue
                    if len(comb) == 1:
                        combinations_map[string] = (comb, None)
                    else:
                        combinations_map[string] = (comb, mode)
                    available.add(string)

        # Preserve the order in which user defined the output combinations
        if whitelist:
            available = reversed([comb for comb in whitelist if comb in available])

        self.available_combinations = deque(available)
        self.combinations_map = combinations_map

    def _get_string_and_set_width(self, combination, mode):
        """
        Construct the string to be displayed and record the max width.
        """
        show = "{}".format(self._separator(mode)).join(combination)
        show = show.rstrip("{}".format(self._separator(mode)))
        self.max_width = max([self.max_width, len(show)])
        return show

    def _choose_what_to_display(self, force_refresh=False):
        """
        Choose what combination to display on the bar.

        By default we try to display the active layout on the first run, else
        we display the last selected combination.
        """
        for _ in range(len(self.available_combinations)):
            if (
                self.displayed is None
                and self.available_combinations[0] == self.active_layout
            ):
                self.displayed = self.available_combinations[0]
                break
            else:
                if self.displayed == self.available_combinations[0]:
                    break
                else:
                    self.available_combinations.rotate(1)
        else:
            if force_refresh:
                self.displayed = self.available_combinations[0]
            else:
                self.py3.log('xrandr error="displayed combination is not available"')

    def _center(self, s):
        """
        Center the given string on the detected max width.
        """
        fmt = "{:^%d}" % self.max_width
        return fmt.format(s)

    def _apply(self, force=False):
        """
        Call xrandr and apply the selected (displayed) combination mode.
        """
        if self.displayed == self.active_layout and not force:
            # no change, do nothing
            return

        combination, mode = self.combinations_map.get(self.displayed, (None, None))
        if combination is None and mode is None:
            # displayed combination cannot be activated, ignore
            return

        cmd = "xrandr"
        outputs = list(self.layout["connected"].keys())
        outputs += list(self.layout["disconnected"].keys())
        previous_output = None
        primary_added = False
        for output in outputs:
            cmd += " --output {}".format(output)
            #
            if output in combination:
                pos = getattr(self, "{}_pos".format(output), "0x0")
                primary = getattr(self, "{}_primary".format(output), None)
                resolution = getattr(self, "{}_mode".format(output), None)
                resolution = "--mode {}".format(resolution) if resolution else "--auto"
                rotation = getattr(self, "{}_rotate".format(output), "normal")
                if rotation not in ["inverted", "left", "normal", "right"]:
                    self.py3.log("configured rotation {} is not valid".format(rotation))
                    rotation = "normal"
                #
                if primary is True and not primary_added:
                    primary_added = True
                    cmd += " --primary"
                if mode == "clone" and previous_output is not None:
                    cmd += " {} --same-as {}".format(resolution, previous_output)
                else:
                    if (
                        "above" in pos
                        or "below" in pos
                        or "left-of" in pos
                        or "right-of" in pos
                    ):
                        cmd += " {} --{} --rotate {}".format(resolution, pos, rotation)
                    else:
                        cmd += " {} --pos {} --rotate {}".format(
                            resolution, pos, rotation
                        )
                previous_output = output
            else:
                cmd += " --off"
        #
        code = self.py3.command_run(cmd)
        if code == 0:
            self.active_comb = combination
            self.active_layout = self.displayed
            self.active_mode = mode
        self.py3.log('command "{}" exit code {}'.format(cmd, code))

        if self.command:
            self.py3.command_run(self.command)

        # move workspaces to outputs as configured
        self._apply_workspaces(combination, mode)

    def _apply_workspaces(self, combination, mode):
        """
        Allows user to force move a comma separated list of workspaces to the
        given output when it's activated.

        Example:
            - DP1_workspaces = "1,2,3"
        """
        if len(combination) > 1 and mode == "extend":
            sleep(3)
            for output in combination:
                workspaces = getattr(self, "{}_workspaces".format(output), "").split(
                    ","
                )
                for workspace in workspaces:
                    if not workspace:
                        continue
                    # switch to workspace
                    cmd = '{} workspace "{}"'.format(self.py3.get_wm_msg(), workspace)
                    self.py3.command_run(cmd)
                    # move it to output
                    cmd = '{} move workspace to output "{}"'.format(
                        self.py3.get_wm_msg(), output
                    )
                    self.py3.command_run(cmd)
                    # log this
                    self.py3.log(
                        "moved workspace {} to output {}".format(workspace, output)
                    )

    def _fallback_to_available_output(self):
        """
        Fallback to the first available output when the active layout
        was composed of only one output.

        This allows us to avoid cases where you get stuck with a black sreen
        on your laptop by switching back to the integrated screen
        automatically !
        """
        if len(self.active_comb) == 1:
            self._choose_what_to_display(force_refresh=True)
            self._apply()
            self.py3.update()

    def _force_force_on_start(self):
        """
        Force the user configured mode on start.
        """
        if self.force_on_start in self.available_combinations:
            self.displayed = self.force_on_start
            self._choose_what_to_display(force_refresh=True)
            self._apply(force=True)
            self.py3.update()
        self.force_on_start = None

    def _separator(self, mode):
        """
        Return the separator for the given mode.
        """
        if mode == "extend":
            return self.icon_extend
        if mode == "clone":
            return self.icon_clone

    def _switch_selection(self, direction):
        self.available_combinations.rotate(direction)
        self.displayed = self.available_combinations[0]

    def _force_on_change(self):
        """
        Handle force_on_change feature.
        """
        for layout in self.force_on_change:
            if layout in self.available_combinations:
                if self.active_layout != layout:
                    self.displayed = layout
                    self._apply(force=True)
                    self.py3.update()
                    break
                else:
                    break

    def on_click(self, event):
        """
        Click events
            - left click & scroll up/down: switch between modes
            - right click: apply selected mode
            - middle click: force refresh of available modes
        """
        self._no_force_on_change = True
        button = event["button"]
        if button == 4:
            self._switch_selection(-1)
        if button in [1, 5]:
            self._switch_selection(1)
        if button == 2:
            self._choose_what_to_display(force_refresh=True)
        if button == 3:
            self._apply()

    def xrandr(self):
        """
        This is the main py3status method, it will orchestrate what's being
        displayed on the bar.
        """
        self.layout = self._get_layout()
        self._set_available_combinations()
        self._choose_what_to_display()

        if len(self.available_combinations) < 2 and self.hide_if_single_combination:
            full_text = self.py3.safe_format(self.format, {"output": ""})
        else:
            if self.fixed_width is True:
                output = self._center(self.displayed)
            else:
                output = self.displayed
            full_text = self.py3.safe_format(self.format, {"output": output})

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }

        # coloration
        if self.displayed == self.active_layout:
            response["color"] = self.py3.COLOR_GOOD
        elif self.displayed not in self.available_combinations:
            response["color"] = self.py3.COLOR_BAD

        # force default layout setup at module startup
        if self.force_on_start is not None:
            sleep(1)
            self._force_force_on_start()

        # follow on change
        if not self._no_force_on_change and self.force_on_change:
            self._force_on_change()

        # this was a click event triggered update
        if self._no_force_on_change:
            self._no_force_on_change = False

        # fallback detection
        if self.active_layout not in self.available_combinations:
            response["color"] = self.py3.COLOR_DEGRADED
            if self.fallback is True:
                self._fallback_to_available_output()

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
