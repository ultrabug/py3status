"""
Native reimplementation of i3status's `read_file` module.

Outputs the contents of the specified file. You can use this to
check contents of files on your system, for example /proc/uptime.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: see placeholders below (default '%content')
    format_bad: format used when path can't be opened
        (default '%title - %errno: %error')
    max_characters: maximum number of characters read from path
        (default 255)
    path: file to read, '~' is expanded (default None)
    title: label available as the %title placeholder (default None)

Format placeholders:
    %title the configured title
    %content the file's content, newlines removed, truncated to
        max_characters
    %errno the errno of the failure to open path
    %error a human readable description of the failure to open path

Color options:
    color_good: path was read successfully
    color_bad: path couldn't be opened

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Real i3status has no 'title' config key - it comes from the
    section's title instead (eg `read_file UPTIME { }` gives
    title="UPTIME"). This module exposes 'title' as an ordinary config
    key instead, so it works with zero config; it's stripped
    automatically if the section resolves to the real i3status
    wrapper, since real i3status crashes on an unrecognized option.

    Both 'title' and 'path' are required, unlike eg ethernet/wireless's
    interface - post_config_hook() raises if either is unset. Real
    i3status prints "error: path not configured" with no color when
    path is unconfigured, but that state is unreachable here.

@author claude
"""

import os

from py3status.i3status.helpers import (
    format_placeholders,
    resolve_cache_timeout,
)


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%content"
    format_bad = "%title - %errno: %error"
    max_characters = 255
    path = None
    title = None

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        missing = [k for k, v in (("title", self.title), ("path", self.path)) if v is None]
        if missing:
            raise Exception(f"missing {', '.join(missing)}")
        self._abs_path = os.path.expanduser(self.path)

    def read_file(self):
        abs_path = self._abs_path
        errno = 0
        content = ""
        ok = False
        try:
            with open(abs_path, "rb") as f:
                content = f.read(self.max_characters).decode(errors="replace")
            ok = True
        except OSError as err:
            errno = err.errno or 0

        content = content.replace("\n", "")

        selected_format = self.format if ok else self.format_bad
        placeholders = [
            ("%title", self.title),
            ("%content", content),
            ("%errno", str(errno)),
            ("%error", os.strerror(errno) if errno else ""),
        ]

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(selected_format, placeholders),
            "color": self.py3.COLOR_GOOD if ok else self.py3.COLOR_BAD,
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
