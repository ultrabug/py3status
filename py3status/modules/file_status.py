# -*- coding: utf-8 -*-
"""
Display if a files or directories exists.

Configuration parameters:
    cache_timeout: how often to run the check (default 10)
    format: format of the output. (default '\?color=paths [\?if=paths ●|■]')
    format_path: format of the path output. (default '{basename}')
    format_path_separator: show separator if more than one (default ' ')
    path: specify a string or a list of paths to check (default None)
    thresholds: specify color thresholds to use (default [(0, 'bad'), (1, 'good')])

Color options:
    color_bad: Error or file/directory does not exist
    color_good: File or directory exists

Format placeholders:
    {format_path} paths of matching files
    {paths} number of paths, eg 1, 2, 3

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

# change color on files match
file_status {
    path = ['/tmp/test*', '~user/test1']
    format = u'\?color=paths ●'
    thresholds = [(0, 'bad'), (1, 'good')]
}
```

@author obb, Moritz Lüdecke, Cyril Levis (@cyrinux)

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf'}

missing
{'color': '#FF0000', 'full_text': u'\u25a0'}
"""

from glob import glob
from os.path import basename, expanduser

ERR_NO_PATH = 'no path given'
DEFAULT_FORMAT = u'\?color=paths [\?if=paths ●|■]'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = DEFAULT_FORMAT
    format_path = u'{basename}'
    format_path_separator = u' '
    path = None
    thresholds = [(0, 'bad'), (1, 'good')]

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

        if not self.path:
            raise Exception(ERR_NO_PATH)

        # backward compatibility, str to list
        if not isinstance(self.path, list):
            self.path = [self.path]
        # expand user paths
        self.path = list(map(expanduser, self.path))

        self.init = {
            'format_path': self.py3.get_placeholders_list(self.format_path)
        }

    def file_status(self):
        # init datas
        paths = sorted([files for path in self.path for files in glob(path)])
        paths_number = len(paths)

        # format paths
        if self.init['format_path']:
            format_path = {}
            format_path_separator = self.py3.safe_format(
                self.format_path_separator)

            for key in self.init['format_path']:
                if key == 'basename':
                    temps_paths = map(basename, paths)
                elif key == 'fullpath':
                    temps_paths = paths
                else:
                    continue
                format_path[key] = self.py3.composite_join(
                    format_path_separator, temps_paths)

            format_path = self.py3.safe_format(self.format_path, format_path)

        # get thresholds
        if self.thresholds:
            self.py3.threshold_get_color(paths_number, 'paths')

        response = {
            'cached_until':
            self.py3.time_in(self.cache_timeout),
            'full_text':
            self.py3.safe_format(self.format, {
                'paths': paths_number,
                'format_path': format_path
            })
        }

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
