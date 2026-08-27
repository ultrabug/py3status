"""
Native reimplementation of i3status's `memory` module.

Gets the memory usage from system on a Linux system from
/proc/meminfo.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    decimals: number of decimals for the human-readable byte values,
        capped at 4 (default 1)
    format: see placeholders below (default '%used %free %available')
    format_degraded: format used when a threshold applies
        (default None, uses format)
    memory_used_method: 'classical' (total - free - buffers - cached) or
        'memavailable' (total - available) (default 'classical')
    threshold_critical: color_bad is used, and format_degraded if set, when
        available memory falls below this value; an integer optionally
        suffixed with T/G/M/K, or a percentage of total memory eg '10%'
        (default None)
    threshold_degraded: same as threshold_critical but using color_degraded
        (default None)
    unit: 'auto', or one of 'B', 'KiB', 'MiB', 'GiB', 'TiB' to fix the unit
        used for the human-readable byte values (default 'auto')

Format placeholders:
    %total total memory
    %used used memory
    %free free memory
    %available available memory
    %shared shared memory
    %percentage_free free memory, in percent
    %percentage_available available memory, in percent
    %percentage_used used memory, in percent
    %percentage_shared shared memory, in percent

Color options:
    color_bad: available memory is below threshold_critical
    color_degraded: available memory is below threshold_degraded

Type: Instance (supports multiple sections via an instance/title)

Notes:
    color_bad takes precedence over color_degraded if both thresholds
    apply.

    If /proc/meminfo can't be read or is missing a required field,
    outputs "can't read memory" with no color, matching real i3status
    exactly.

@author claude
"""

from py3status.i3status.helpers import (
    format_placeholders,
    resolve_cache_timeout,
)

BINARY_BASE = 1024
IEC_SYMBOLS = ["B", "KiB", "MiB", "GiB", "TiB"]
MAX_DECIMALS = 4

MEMINFO_FIELDS = {
    "MemTotal:": "total",
    "MemFree:": "free",
    "MemAvailable:": "available",
    "Buffers:": "buffers",
    "Cached:": "cached",
    "Shmem:": "shared",
}


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    decimals = 1
    format = "%used %free %available"
    format_degraded = None
    memory_used_method = "classical"
    threshold_critical = None
    threshold_degraded = None
    unit = "auto"

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        self._threshold_degraded = (
            self._parse_threshold(self.threshold_degraded) if self.threshold_degraded else None
        )
        self._threshold_critical = (
            self._parse_threshold(self.threshold_critical) if self.threshold_critical else None
        )

    @staticmethod
    def _read_meminfo():
        values = {}
        with open("/proc/meminfo") as f:
            for line in f:
                for prefix, key in MEMINFO_FIELDS.items():
                    if line.startswith(prefix):
                        # values are in kB; convert to bytes
                        values[key] = int(line[len(prefix) :].split()[0]) * 1024
                        break
                if len(values) == len(MEMINFO_FIELDS):
                    break
        return values

    @staticmethod
    def _print_bytes_human(num_bytes, unit, decimals):
        base = float(num_bytes)
        exponent = 0
        while base >= BINARY_BASE and exponent < len(IEC_SYMBOLS) - 1:
            if unit.lower() == IEC_SYMBOLS[exponent].lower():
                break
            base /= BINARY_BASE
            exponent += 1
        prec = min(decimals, MAX_DECIMALS)
        return f"{base:.{prec}f} {IEC_SYMBOLS[exponent]}"

    @staticmethod
    def _print_percentage(percent):
        return f"{percent:.1f}%"

    @staticmethod
    def _parse_threshold(amount_str):
        """Parse '10%', '500M', '2G', etc. into (amount, unit) - unit is '%',
        'k'/'m'/'g'/'t', or '' for a plain byte count. Config is static, so
        this only needs to run once, in post_config_hook()."""
        digits = ""
        for char in amount_str:
            if char.isdigit():
                digits += char
            else:
                break
        amount = int(digits) if digits else 0
        suffix = amount_str[len(digits) :].strip()
        unit = suffix[0].lower() if suffix else ""
        return amount, unit

    @staticmethod
    def _threshold_bytes(parsed, mem_total):
        """Apply a pre-parsed (amount, unit) threshold against a live mem_total
        (bytes) - the only part of this that must run every tick."""
        amount, unit = parsed
        if unit == "%":
            return mem_total * amount // 100
        multiplier = {"k": 1, "m": 2, "g": 3, "t": 4}.get(unit)
        if multiplier is not None:
            return amount * (BINARY_BASE**multiplier)
        return amount

    def memory(self):
        try:
            meminfo = self._read_meminfo()
            total = meminfo["total"]
            free = meminfo["free"]
            available = meminfo["available"]
            buffers = meminfo["buffers"]
            cached = meminfo["cached"]
            shared = meminfo["shared"]
        except (OSError, KeyError):
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": "can't read memory",
            }

        if self.memory_used_method == "memavailable":
            used = total - available
        else:
            used = total - free - buffers - cached

        selected_format = self.format
        color = None

        if self._threshold_degraded and available < self._threshold_bytes(
            self._threshold_degraded, total
        ):
            color = self.py3.COLOR_DEGRADED
        if self._threshold_critical and available < self._threshold_bytes(
            self._threshold_critical, total
        ):
            color = self.py3.COLOR_BAD

        if color and self.format_degraded is not None:
            selected_format = self.format_degraded

        placeholders = [
            ("%total", self._print_bytes_human(total, self.unit, self.decimals)),
            ("%used", self._print_bytes_human(used, self.unit, self.decimals)),
            ("%free", self._print_bytes_human(free, self.unit, self.decimals)),
            ("%available", self._print_bytes_human(available, self.unit, self.decimals)),
            ("%shared", self._print_bytes_human(shared, self.unit, self.decimals)),
            ("%percentage_free", self._print_percentage(100.0 * free / total)),
            ("%percentage_available", self._print_percentage(100.0 * available / total)),
            ("%percentage_used", self._print_percentage(100.0 * used / total)),
            ("%percentage_shared", self._print_percentage(100.0 * shared / total)),
        ]

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(selected_format, placeholders),
        }
        if color:
            response["color"] = color
        return response


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
