"""
Native reimplementation of i3status's `cpu_usage` module.

Gets the percentual CPU usage from /proc/stat.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    degraded_threshold: usage percentage at/above which color_degraded is
        used (default 90)
    format: see placeholders below (default '%usage')
    format_above_degraded_threshold: format used when usage is at/above
        degraded_threshold but below max_threshold
        (default None, uses format)
    format_above_threshold: format used when usage is at/above
        max_threshold (default None, uses format)
    max_threshold: usage percentage at/above which color_bad is used
        (default 95)

Format placeholders:
    %usage overall CPU usage, across all CPUs
    %cpu0, %cpu1, ... usage of an individual CPU, starting from %cpu0

Usage is the percentage of non-idle time since the previous call; the
first ever call reports the average usage since boot, matching i3status.

Color options:
    color_bad: usage is at/above max_threshold
    color_degraded: usage is at/above degraded_threshold

Type: Singleton (supports only one, unnamed section)

Notes:
    color_bad takes precedence over color_degraded if both thresholds
    apply.

    Real i3status also supports FreeBSD/OpenBSD via sysctl(3); this
    module only reads Linux's /proc/stat.

    If path can't be read, outputs "cant read cpu usage" with no
    color, matching real i3status.

    'path' is a real i3status option here (cfg_opt_t usage_opts,
    default '/proc/stat') absent from the man page for unknown reasons.
    This module supports it if set, but deliberately leaves it out of
    'Configuration parameters' above and off the class body so it
    isn't advertised - it exists purely so tests can point it at a
    fixture file instead of the real /proc/stat.

@author claude
"""

import re

from py3status.i3status.helpers import resolve_cache_timeout

CPU_LINE_RE = re.compile(r"^cpu(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)")
PLACEHOLDER_RE = re.compile(r"%(usage|cpu\d+)")


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    degraded_threshold = 90
    format = "%usage"
    format_above_degraded_threshold = None
    format_above_threshold = None
    max_threshold = 95

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        # undocumented, real i3status option (see Notes above) - support it
        # if a user (or a test) sets it, without advertising it as a
        # supported config key
        self.path = getattr(self, "path", "/proc/stat")
        self._prev_stats = None

    @staticmethod
    def _read_cpu_stats(path):
        """Return {cpu_index: (user, nice, system, idle, total)}."""
        stats = {}
        with open(path) as f:
            next(f)  # skip the aggregate "cpu " line
            for line in f:
                match = CPU_LINE_RE.match(line)
                if not match:
                    break
                idx, user, nice, system, idle = (int(x) for x in match.groups())
                stats[idx] = (user, nice, system, idle, user + nice + system + idle)
        return stats

    @staticmethod
    def _usage_percent(prev, curr):
        prev_idle, prev_total = prev[3], prev[4]
        curr_idle, curr_total = curr[3], curr[4]
        diff_idle = curr_idle - prev_idle
        diff_total = curr_total - prev_total
        if not diff_total:
            return 0
        return (1000 * (diff_total - diff_idle) // diff_total + 5) // 10

    def cpu_usage(self):
        try:
            curr_stats = self._read_cpu_stats(self.path)
        except OSError:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": "cant read cpu usage",
            }
        prev_stats = self._prev_stats or {idx: (0, 0, 0, 0, 0) for idx in curr_stats}

        zero = (0, 0, 0, 0, 0)
        per_cpu_usage = {
            idx: self._usage_percent(prev_stats.get(idx, zero), curr_stats[idx])
            for idx in curr_stats
        }

        prev_all = (
            tuple(sum(values) for values in zip(*prev_stats.values())) if prev_stats else zero
        )
        curr_all = tuple(sum(values) for values in zip(*curr_stats.values()))
        usage = self._usage_percent(prev_all, curr_all)

        self._prev_stats = curr_stats

        color = None
        selected_format = self.format
        if usage >= self.max_threshold:
            color = self.py3.COLOR_BAD
            if self.format_above_threshold is not None:
                selected_format = self.format_above_threshold
        elif usage >= self.degraded_threshold:
            color = self.py3.COLOR_DEGRADED
            if self.format_above_degraded_threshold is not None:
                selected_format = self.format_above_degraded_threshold

        def substitute(match):
            name = match.group(1)
            if name == "usage":
                return f"{usage:02d}%"
            cpu_index = int(name[3:])
            if cpu_index not in per_cpu_usage:
                return ""
            return f"{per_cpu_usage[cpu_index]:02d}%"

        full_text = PLACEHOLDER_RE.sub(substitute, selected_format)

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }
        if color:
            response["color"] = color
        return response


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
