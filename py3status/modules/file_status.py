# -*- coding: utf-8 -*-
"""
Display if a file or directory exists.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format: format of the output. (default '{icon} {format_path}')
    format_path: format of the path output. (default '{basename}')
    format_path_separator: show separator if more than one (default ' ')
    icon_available: icon to display when available (default '●')
    icon_unavailable: icon to display when unavailable (default '■')
    path: the path(s) to a file or dir to check if it exists, take a list (default None)

Color options:
    color_bad: Error or file/directory does not exist
    color_good: File or directory exists

Format placeholders:
    {format_path} paths of matching files
    {icon} icon for the current availability

format_path path placeholders:
    {basename} basename of matching files
    {fullpath} fullpath of matching files

Examples:
```
# check files with wildcard, or contain user path, full paths
file_status {
    path = ['/tmp/test*', '~user/test1']
    format_path = '{fullpath}'
}
```

@author obb, Moritz Lüdecke, Cyril Levis (@cyrinux)

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf test.py'}

missing
{'color': '#FF0000', 'full_text': u'\u25a0'}
"""

from glob import glob
from itertools import chain
from os.path import basename, expanduser

ERR_NO_PATH = 'no path given'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = u'{icon} {format_path}'
    format_path = u'{basename}'
    format_path_separator = u' '
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
            if not isinstance(self.path, list):
                self.path = [self.path]
            # expand user paths
            self.path = list(map(expanduser, self.path))

    def file_status(self):
        if self.path is None:
            return {
                'color': self.py3.COLOR_ERROR or self.py3.COLOR_BAD,
                'full_text': ERR_NO_PATH,
                'cached_until': self.py3.CACHE_FOREVER,
            }

        # init data
        file_status_data = {}
        # expand glob from paths
        paths = list(map(glob, self.path))
        # merge list of paths
        paths = [x for x in chain.from_iterable(paths)]

        # fill data
        file_status_data['icon'] = self.icon_unavailable
        color = self.py3.COLOR_BAD

        if paths:
            file_status_data['icon'] = self.icon_available
            color = self.py3.COLOR_GOOD

        # format paths
        if self.format_path:
            format_path = {}

            format_path_separator = self.py3.safe_format(
                self.format_path_separator)

            format_path['basename'] = self.py3.composite_join(
                format_path_separator, map(basename, paths))

            format_path['full'] = self.py3.composite_join(
                format_path_separator, paths)

            file_status_data['format_path'] = self.py3.safe_format(
                self.format_path, format_path)

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, file_status_data),
            'color': color
        }

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
