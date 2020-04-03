"""
Display status of a process on your system.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{icon}')
    full: match against the full command line (default False)
    icon_off: show this if a process is not running (default '■')
    icon_on: show this if a process is running (default '●')
    process: specify a process name to use (default None)

Format placeholders:
    {icon} process icon
    {process} process name

Color options:
    color_bad: Not running
    color_good: Running

@author obb, Moritz Lüdecke

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf'}

not_running
{'color': '#FF0000', 'full_text': u'\u25a0'}
"""

STRING_ERROR = "missing process"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{icon}"
    full = False
    icon_off = "■"
    icon_on = "●"
    process = None

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "format_running",
                    "new": "icon_on",
                    "msg": "obsolete parameter use `icon_on`",
                },
                {
                    "param": "format_not_running",
                    "new": "icon_off",
                    "msg": "obsolete parameter use `icon_off`",
                },
            ]
        }

    def post_config_hook(self):
        if not self.process:
            raise Exception(STRING_ERROR)
        self.color_on = self.py3.COLOR_ON or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_OFF or self.py3.COLOR_BAD
        self.pgrep_command = ["pgrep", self.process]
        if self.full:
            self.pgrep_command.insert(1, "-f")

    def _is_running(self):
        try:
            self.py3.command_output(self.pgrep_command)
            return True
        except self.py3.CommandError:
            return False

    def process_status(self):
        if self._is_running():
            icon = self.icon_on
            color = self.color_on
        else:
            icon = self.icon_off
            color = self.color_off

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": color,
            "full_text": self.py3.safe_format(
                self.format, {"icon": icon, "process": self.process}
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
