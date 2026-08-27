"""
Native reimplementation of i3status's `path_exists` module.

Checks if the given path exists in the filesystem. You can use this
to check if something is active, like for example a VPN tunnel
managed by NetworkManager.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: see placeholders below (default '%title: %status')
    format_down: format used when path doesn't exist
        (default None, uses format)
    path: filesystem path to check (default None)
    title: label available as the %title placeholder (default None)

Format placeholders:
    %title the configured title
    %status 'yes' if path exists, 'no' otherwise

Color options:
    color_good: path exists
    color_bad: path doesn't exist

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Real i3status has no 'title' config key - it comes from the
    section's title instead (eg `path_exists VPN { }` gives
    title="VPN" - the "X: no" example below is really just the section
    title showing through). This module exposes 'title' as an ordinary
    config key instead, so it works with zero config; it's stripped
    automatically if the section resolves to the real i3status
    wrapper, since real i3status crashes on an unrecognized option.

    Both 'title' and 'path' are required - post_config_hook() raises if
    either is unset. Real i3status has no distinct error styling for a
    missing path either: it silently renders an empty %status-driven
    "no" (uncolored) instead.

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
    format = "%title: %status"
    format_down = None
    path = None
    title = None

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        missing = [k for k, v in (("title", self.title), ("path", self.path)) if v is None]
        if missing:
            raise Exception(f"missing {', '.join(missing)}")

    def path_exists(self):
        exists = os.path.exists(self.path)

        selected_format = self.format if exists or self.format_down is None else self.format_down
        placeholders = [("%title", self.title), ("%status", "yes" if exists else "no")]

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(selected_format, placeholders),
            "color": self.py3.COLOR_GOOD if exists else self.py3.COLOR_BAD,
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
