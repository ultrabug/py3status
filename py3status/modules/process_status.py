# -*- coding: utf-8 -*-
"""
Display if a process is running.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: default format for this module (default '{icon}')
    full: if True, match against full command line (default False)
    icon_off: show when process not running (default '■')
    icon_on: show when process running (default '●')
    process: process name to check for (default None)

Format placeholders:
    {icon} process icon
    {process} process name

Color options:
    color_bad: Not running
    color_good: Running

@author obb, Moritz Lüdecke

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf'}

off
{'color': '#FF0000', 'full_text': u'\u25a0'}
"""
STRING_ERROR = 'process_status: N/A'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{icon}'
    full = False
    icon_off = u'■'
    icon_on = u'●'
    process = None

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'format_running',
                    'new': 'icon_on',
                    'msg': 'obsolete parameter use `icon_on`',
                },
                {
                    'param': 'format_not_running',
                    'new': 'icon_off',
                    'msg': 'obsolete parameter use `icon_off`',
                },
            ],
        }

    def post_config_hook(self):
        self.color_on = self.py3.COLOR_ON or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_OFF or self.py3.COLOR_BAD

    def _is_running(self):
        try:
            pgrep = ["pgrep", self.process]
            if self.full:
                pgrep = ["pgrep", "-f", self.process]
            self.py3.command_output(pgrep)
            return True
        except:
            return False

    def process_status(self):
        if self.process is None:
            return {
                'cached_until': self.py3.CACHE_FOREVER,
                'color': self.py3.COLOR_BAD,
                'full_text': STRING_ERROR
            }

        if self._is_running():
            icon = self.icon_on
            color = self.color_on
        else:
            icon = self.icon_off
            color = self.color_off

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
            'full_text': self.py3.safe_format(
                self.format, {'icon': icon, 'process': self.process})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
