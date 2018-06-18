# -*- coding: utf-8 -*-
"""
Display if a files or directories exists.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format: format of the output. (default '\?if=paths ●|■')
    format_path: format of the path output. (default '{basename}')
    format_path_separator: show separator if more than one (default ' ')
    path: the path(s) to a file or dir to check if it exists, take a list (default None)

Color options:
    color_bad: Error or file/directory does not exist
    color_good: File or directory exists

Format placeholders:
    {format_path} paths of matching files

format_path path placeholders:
    {basename} basename of matching files
    {fullpath} fullpath of matching files

Examples:
```
# check files with wildcard, or contain user path, full paths
file_status {
    path = ['/tmp/test*', '~user/test1']
    format = u'\?if=paths ● {format_path}|■ no files found'
    format_path = '{fullpath}'
}
```

@author obb, Moritz Lüdecke, Cyril Levis (@cyrinux), @lasers

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf test.py'}

missing
{'color': '#FF0000', 'full_text': u'\u25a0'}
"""

from glob import glob
from os.path import basename, expanduser

ERR_NO_PATH = 'no path given'
DEFAULT_FORMAT = u'\?if=paths ●|■'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = DEFAULT_FORMAT
    format_path = u'{basename}'
    format_path_separator = u' '
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
        # deprecation
        on = getattr(self, 'icon_available', None)
        off = getattr(self, 'icon_unavailable', None)
        if self.format == DEFAULT_FORMAT and (on or off):
            self.format = u'\?if=paths {}|{}'.format(on or u'●', off or u'■')
            msg = 'DEPRECATION: you are using old style configuration '
            msg += 'parameters you should update to use the new format.'
            self.py3.log(msg)

        if self.path:
            # backward compatibility, str to list
            if not isinstance(self.path, list):
                self.path = [self.path]
            # expand user paths
            self.path = list(map(expanduser, self.path))

            self.init = {'format_path': []}
            for x in set(self.py3.get_placeholders_list(self.format_path)):
                self.init['format_path'].append(x)

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
        paths = sorted([files for path in self.path for files in glob(path)])
        file_status_data['paths'] = len(paths)

        # fill data, legacy stuff
        color = self.py3.COLOR_BAD
        if paths:
            color = self.py3.COLOR_GOOD

        # format paths
        if self.init['format_path']:
            self.format_path_separator = self.py3.safe_format(self.format_path_separator)

            format_path = {}

            if 'basename' in self.init['format_path']:
                format_path['basename'] = map(basename, paths)

            if 'fullpath' in self.init['format_path']:
                format_path['fullpath'] = paths

            for x in self.init['format_path']:
                format_path[x] = self.py3.composite_join(
                    self.format_path_separator, format_path[x]
                )

            file_status_data['format_path'] = self.py3.safe_format(
                self.format_path, format_path
            )

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
