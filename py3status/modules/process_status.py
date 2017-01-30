# -*- coding: utf-8 -*-
"""
Display if a process is running.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: default format for this module (default '{icon}')
    full: if True, match against the full command line (default False)
    icon_off: display when the process is not running (default '■')
    icon_on: display when the process is running (default '●')
    process: the process name to check if it is running (default None)
    string_unavailable: no process name (default 'process_status: N/A')

Format placeholders:
    {icon} process icon
    {process} process name

Color options:
    color_bad: process currently not running or unavailable
    color_good: process currently running

@author obb, Moritz Lüdecke
"""


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
    string_unavailable = 'process_status: N/A'

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
        pgrep = ["pgrep", self.process]

        if self.full:
            pgrep = ["pgrep", "-f", self.process]
        try:
            self.py3.command_output(pgrep)
        except:
            return False
        else:
            return True

    def process_status(self):
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        if self.process is None:
            response['cached_until'] = self.py3.CACHE_FOREVER
            response['color'] = self.py3.COLOR_BAD
            response['full_text'] = self.string_unavailable
        else:
            run = self._is_running()
            icon = self.icon_on if run else self.icon_off

            response['color'] = self.color_on if run else self.color_off
            response['full_text'] = self.py3.safe_format(self.format, {'icon': icon,
                                                         'process': self.process}),

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
