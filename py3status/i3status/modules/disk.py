"""
Native reimplementation of i3status's `disk` module.

Gets used, free, available and total amount of bytes on the given
mounted filesystem.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: see placeholders below (default '%free')
    format_below_threshold: format used when low_threshold applies
        (default None, uses format)
    format_not_mounted: format used when path isn't a mount point
        (default '')
    low_threshold: value (interpreted per threshold_type) below which
        color_bad is used; 0 disables this (default 0)
    path: filesystem path to check (default '/')
    prefix_type: 'binary' (Ki/Mi/Gi/Ti), 'decimal' (k/M/G/T) or 'custom'
        (K/M/G/T using a binary base) (default 'binary')
    threshold_type: one of 'percentage_free', 'percentage_avail',
        'bytes_free', 'bytes_avail', or a value prefixed with an iec
        symbol (T/G/M/K) followed by '_bytes_free'/'_bytes_avail'
        (default 'percentage_avail')

Format placeholders:
    %free the free disk space
    %used the used disk space
    %total the total disk space
    %avail the available (non-reserved) disk space
    %percentage_free free space, in percent
    %percentage_used_of_avail used space relative to available, in percent
    %percentage_used used space, in percent
    %percentage_avail available space, in percent

Color options:
    color_bad: value (per threshold_type) is below low_threshold
        (0 disables this)

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Real i3status has no 'path' config key - it comes from the
    section's title instead (eg `disk "/" { }` gives path="/"). This
    module exposes 'path' as an ordinary config key instead, so it
    works with zero config; it's stripped automatically if the section
    resolves to the real i3status wrapper, since real i3status crashes
    on an unrecognized option.

@author claude
"""

import os

from py3status.i3status.helpers import (
    format_placeholders,
    resolve_cache_timeout,
)

BINARY_BASE = 1024
DECIMAL_BASE = 1000
MAX_EXPONENT = 4

IEC_SYMBOLS = ["", "Ki", "Mi", "Gi", "Ti"]
SI_SYMBOLS = ["", "k", "M", "G", "T"]
CUSTOM_SYMBOLS = ["", "K", "M", "G", "T"]


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%free"
    format_below_threshold = None
    format_not_mounted = ""
    low_threshold = 0
    path = "/"
    prefix_type = "binary"
    threshold_type = "percentage_avail"

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        self.prefix_type = (self.prefix_type or "").lower()
        self.threshold_type = (self.threshold_type or "").lower()

    @staticmethod
    def _format_bytes(num_bytes, base, symbols):
        size = float(num_bytes)
        exponent = 0
        while size >= base and exponent < MAX_EXPONENT:
            size /= base
            exponent += 1
        return f"{size:.1f} {symbols[exponent]}B"

    def _print_bytes_human(self, num_bytes, prefix_type):
        """prefix_type must already be normalized (lowercased) by the caller."""
        if prefix_type == "decimal":
            return self._format_bytes(num_bytes, DECIMAL_BASE, SI_SYMBOLS)
        elif prefix_type == "custom":
            return self._format_bytes(num_bytes, BINARY_BASE, CUSTOM_SYMBOLS)
        return self._format_bytes(num_bytes, BINARY_BASE, IEC_SYMBOLS)

    @staticmethod
    def _below_threshold(stat, prefix_type, threshold_type, low_threshold):
        """prefix_type/threshold_type must already be normalized (lowercased)
        by the caller."""
        frsize, blocks, bfree, bavail = stat.f_frsize, stat.f_blocks, stat.f_bfree, stat.f_bavail

        if threshold_type == "percentage_free":
            return 100.0 * bfree / blocks < low_threshold
        elif threshold_type == "percentage_avail":
            return 100.0 * bavail / blocks < low_threshold
        elif threshold_type == "bytes_free":
            return frsize * bfree < low_threshold
        elif threshold_type == "bytes_avail":
            return frsize * bavail < low_threshold
        elif len(threshold_type) > 6 and threshold_type[1:] in ("bytes_free", "bytes_avail"):
            base = DECIMAL_BASE if prefix_type == "decimal" else BINARY_BASE
            factor = {"t": base**4, "g": base**3, "m": base**2, "k": base}.get(threshold_type[0])
            if factor is None:
                return False
            if threshold_type[1:] == "bytes_free":
                return frsize * bfree < low_threshold * factor
            return frsize * bavail < low_threshold * factor
        return False

    def disk(self):
        selected_format = self.format
        color = None

        try:
            stat = os.statvfs(self.path)
            mounted = True
        except OSError:
            mounted = False

        if not mounted:
            selected_format = self.format_not_mounted
        elif self.low_threshold > 0 and self._below_threshold(
            stat, self.prefix_type, self.threshold_type, self.low_threshold
        ):
            color = self.py3.COLOR_BAD
            if self.format_below_threshold is not None:
                selected_format = self.format_below_threshold

        if mounted:
            free_bytes = stat.f_frsize * stat.f_bfree
            used_bytes = stat.f_frsize * (stat.f_blocks - stat.f_bfree)
            total_bytes = stat.f_frsize * stat.f_blocks
            avail_bytes = stat.f_frsize * stat.f_bavail
            placeholders = [
                ("%free", self._print_bytes_human(free_bytes, self.prefix_type)),
                ("%used", self._print_bytes_human(used_bytes, self.prefix_type)),
                ("%total", self._print_bytes_human(total_bytes, self.prefix_type)),
                ("%avail", self._print_bytes_human(avail_bytes, self.prefix_type)),
                ("%percentage_free", f"{100.0 * stat.f_bfree / stat.f_blocks:.1f}%"),
                (
                    "%percentage_used_of_avail",
                    f"{100.0 * (stat.f_blocks - stat.f_bavail) / stat.f_blocks:.1f}%",
                ),
                (
                    "%percentage_used",
                    f"{100.0 * (stat.f_blocks - stat.f_bfree) / stat.f_blocks:.1f}%",
                ),
                ("%percentage_avail", f"{100.0 * stat.f_bavail / stat.f_blocks:.1f}%"),
            ]
            full_text = format_placeholders(selected_format, placeholders)
        else:
            full_text = selected_format

        response = {"cached_until": self.py3.time_in(self.cache_timeout), "full_text": full_text}
        if color:
            response["color"] = color
        return response


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
