"""
Control screen rotation.

Configuration parameters:
    cache_timeout: how often to refresh this module.
        (default 10)
    format: a string that formats the output, can include placeholders.
        (default '{icon}')
    hide_if_disconnected: a boolean flag to hide icon when `screen` is
        disconnected.
        It has no effect unless `screen` option is also configured.
        (default False)
    horizontal_icon: a character to represent horizontal rotation.
        (default 'H')
    horizontal_rotation: a horizontal rotation for xrandr to use.
        Available options: 'normal' or 'inverted'.
        (default 'normal')
    screen: display output name to rotate, as detected by xrandr.
        If not provided, all enabled screens will be rotated.
        (default None)
    vertical_icon: a character to represent vertical rotation.
        (default 'V')
    vertical_rotation: a vertical rotation for xrandr to use.
        Available options: 'left' or 'right'.
        (default 'left')

Format placeholders:
    {icon} a rotation icon, specified by `horizontal_icon` or `vertical_icon`.
    {screen} a screen name, specified by `screen` option or detected
        automatically if only one screen is connected, otherwise 'ALL'.

Color options:
    color_degraded: Screen is disconnected
    color_good: Displayed rotation is active

@author Maxim Baz (https://github.com/maximbaz)
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'H'}

vertical
{'full_text': u'V'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{icon}"
    hide_if_disconnected = False
    horizontal_icon = "H"
    horizontal_rotation = "normal"
    screen = None
    vertical_icon = "V"
    vertical_rotation = "left"

    def post_config_hook(self):
        self.displayed = ""
        self.scrolling = False

    def _get_active_outputs(self):
        data = self.py3.command_output(["xrandr"]).splitlines()
        connected_outputs = [x.split() for x in data if " connected" in x]
        active_outputs = []
        for output in connected_outputs:
            for x in output[2:]:
                if "x" in x and "+" in x:
                    active_outputs.append(output[0])
                    break
                elif "(" in x:
                    break
        return active_outputs

    def _get_current_rotation_icon(self, all_outputs):
        data = self.py3.command_output(["xrandr"]).splitlines()
        output = self.screen or all_outputs[0]
        output_line = "".join(x for x in data if x.startswith(output))

        for x in output_line.split():
            if "normal" in x or "inverted" in x:
                return self.horizontal_icon
            elif "left" in x or "right" in x:
                return self.vertical_icon

    def _apply(self):
        if self.displayed == self.horizontal_icon:
            rotation = self.horizontal_rotation
        else:
            rotation = self.vertical_rotation
        cmd = "xrandr"
        outputs = [self.screen] if self.screen else self._get_active_outputs()
        for output in outputs:
            cmd += f" --output {output} --rotate {rotation}"
        self.py3.command_run(cmd)

    def _switch_selection(self):
        if self.displayed == self.horizontal_icon:
            self.displayed = self.vertical_icon
        else:
            self.displayed = self.horizontal_icon

    def xrandr_rotate(self):
        all_outputs = self._get_active_outputs()
        selected_screen_disconnected = (
            self.screen is not None and self.screen not in all_outputs
        )
        if selected_screen_disconnected and self.hide_if_disconnected:
            self.displayed = ""
            full_text = ""
        else:
            if not self.scrolling:
                self.displayed = self._get_current_rotation_icon(all_outputs)

            if self.screen or len(all_outputs) == 1:
                screen = self.screen or all_outputs[0]
            else:
                screen = "ALL"
            full_text = self.py3.safe_format(
                self.format, dict(icon=self.displayed or "?", screen=screen)
            )

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }

        # coloration
        if selected_screen_disconnected and not self.hide_if_disconnected:
            response["color"] = self.py3.COLOR_DEGRADED
        elif self.displayed == self._get_current_rotation_icon(all_outputs):
            response["color"] = self.py3.COLOR_GOOD

        self.scrolling = False
        return response

    def on_click(self, event):
        """
        Click events
            - left click & scroll up/down: switch between rotations
            - right click: apply selected rotation
        """
        button = event["button"]
        if button in [1, 4, 5]:
            self.scrolling = True
            self._switch_selection()
        elif button == 3:
            self._apply()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
