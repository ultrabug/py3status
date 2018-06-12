# -*- coding: utf-8 -*-
"""
Display if a file or directory exists.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format: format of the output. (default '{icon}')
    icon_available: icon to display when available (default '●')
    icon_unavailable: icon to display when unavailable (default '■')
    path: the path(s) to a file or dir to check if it exists, take a list (default None)

Color options:
    color_bad: Error or file/directory does not exist
    color_good: File or directory exists

Format placeholders:
    {icon} icon for the current availability

@author obb, Moritz Lüdecke

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf'}

missing
{'color': '#FF0000', 'full_text': u'\u25a0'}
"""

from glob import glob
from itertools import chain
from os.path import expanduser

ERR_NO_PATH = 'no path given'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{icon}'
    icon_available = u'●'
    icon_unavailable = u'■'
    path = None

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'format_available',
                    'new': 'icon_available',
                    'msg': 'obsolete parameter use `icon_available`'
                },
                {
                    'param': 'format_unavailable',
                    'new': 'icon_unavailable',
                    'msg': 'obsolete parameter use `icon_unavailable`'
                },
            ],
        }

    def post_config_hook(self):
        if self.path:
            # backward compatibility, str to list
            if isinstance(self.path, str):
                self.path = [self.path]
            # expand user paths
            self.path = [*map(expanduser, self.path)]

    def file_status(self):
        if self.path is None:
            return {
                'color': self.py3.COLOR_ERROR or self.py3.COLOR_BAD,
                'full_text': ERR_NO_PATH,
                'cached_until': self.py3.CACHE_FOREVER,
            }

        # expand user to paths
        paths = [*map(glob, self.path)]
        # merge list of paths
        paths = [x for x in chain.from_iterable(paths)]

        icon = self.icon_unavailable
        color = self.py3.COLOR_BAD

        if paths:
            icon = self.icon_available
            color = self.py3.COLOR_GOOD

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'icon': icon}),
            'color': color
        }

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
