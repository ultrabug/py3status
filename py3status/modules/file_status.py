"""
Display if files or directories exists.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module
        (default '\\?color=path [\\?if=path ●|■]')
    format_path: format for paths (default '{basename}')
    format_path_separator: show separator if more than one (default ' ')
    paths: specify a string or a list of paths to check (default None)
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (1, 'good')])

Format placeholders:
    {format_path} format for paths
    {path} number of paths, eg 1, 2, 3

format_path placeholders:
    {basename} basename of pathname
    {pathname} pathname

Color options:
    color_bad: files or directories does not exist
    color_good: files or directories exists

Color thresholds:
    format:
        path: print a color based on the number of paths

Examples:
```
# add multiple paths with wildcard or with pathnames
file_status {
    paths = ['/tmp/test*', '~user/test1', '~/Videos/*.mp4']
}

# colorize basenames
file_status {
    paths = ['~/.config/i3/modules/*.py']
    format = '{format_path}'
    format_path = '\\?color=good {basename}'
    format_path_separator = ', '
}
```

@author obb, Moritz Lüdecke, Cyril Levis (@cyrinux)

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'\u25cf'}

missing
{'color': '#FF0000', 'full_text': u'\u25a0'}
"""

from pathlib import Path


STRING_NO_PATHS = "missing paths"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "\\?color=path [\\?if=path \u25cf|\u25a0]"
    format_path = "{basename}"
    format_path_separator = " "
    paths = None
    thresholds = [(0, "bad"), (1, "good")]

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "format_available",
                    "new": "icon_available",
                    "msg": "obsolete parameter use `icon_available`",
                },
                {
                    "param": "format_unavailable",
                    "new": "icon_unavailable",
                    "msg": "obsolete parameter use `icon_unavailable`",
                },
                {
                    "param": "path",
                    "new": "paths",
                    "msg": "obsolete parameter use `paths`",
                },
            ],
            "rename_placeholder": [
                {"placeholder": "paths", "new": "path", "format_strings": ["format"]}
            ],
        }

    def post_config_hook(self):
        if not self.paths:
            raise Exception(STRING_NO_PATHS)

        # icon deprecation
        on = getattr(self, "icon_available", "\u25cf")
        off = getattr(self, "icon_unavailable", "\u25a0")
        new_icon = fr"\?color=path [\?if=path {on}|{off}]"
        self.format = self.format.replace("{icon}", new_icon)

        # convert str to list + expand path
        if not isinstance(self.paths, list):
            self.paths = [self.paths]
        self.paths = [Path(path).expanduser() for path in self.paths]

        self.init = {"format_path": []}
        if self.py3.format_contains(self.format, "format_path"):
            self.init["format_path"] = self.py3.get_placeholders_list(self.format_path)

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def file_status(self):
        # init data
        paths = sorted(
            files for path in self.paths for files in path.parent.glob(path.name)
        )
        count_path = len(paths)
        format_path = None

        # format paths
        if self.init["format_path"]:
            new_data = []
            format_path_separator = self.py3.safe_format(self.format_path_separator)

            for pathname in paths:
                path = {}
                for key in self.init["format_path"]:
                    if key == "basename":
                        value = pathname.name
                    elif key == "pathname":
                        value = pathname
                    else:
                        continue
                    path[key] = self.py3.safe_format(value)
                new_data.append(self.py3.safe_format(self.format_path, path))

            format_path = self.py3.composite_join(format_path_separator, new_data)

        for x in self.thresholds_init:
            if x in ["path", "paths"]:
                self.py3.threshold_get_color(count_path, x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format,
                {"path": count_path, "paths": count_path, "format_path": format_path},
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
