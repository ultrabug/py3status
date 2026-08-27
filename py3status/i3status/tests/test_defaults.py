"""Cross-module test: every module's config defaults vs real i3status."""

import pytest

# The tables below pin down every module's *default* config values against
# real i3status 2.15's own cfg_opt_t defaults (extracted from i3status.c's
# option tables and cross-checked with `order += "<module>"` and no config
# block at all, run through the real binary via i3status_diff.py).
#
# Two things fell out of building this table that are worth recording:
#
# - For "titled" modules (anything using CFGF_TITLE|CFGF_MULTI in real
#   i3status: battery, disk, cpu_temperature, ethernet, wireless, tztime,
#   volume, run_watch, path_exists, read_file), a bare `order += "X"` with
#   no matching `X { }`/`X "title" { }` section makes real i3status print
#   *nothing at all* for that entry - cfg_gettsec() returns NULL and the
#   module is never even instantiated. Confirmed directly:
#   i3status_diff.py 'order += "battery 0"'   -> '\n' (empty line)
#   i3status_diff.py 'order += "disk /"'      -> '\n' (empty line)
#   py3status has no equivalent "config section entirely absent" concept -
#   every discovered module always runs on its Python class defaults. This
#   is intentional (see the "zero configuration required" project goal),
#   not a bug, but it is a real, permanent behavioral difference from real
#   i3status in this specific bare-order-only scenario.
#
# - A few modules key off the config section's *title* in real i3status
#   with no corresponding config key at all (disk's path, cpu_temperature's
#   zone, ethernet/wireless's interface). Those are intentionally excluded
#   below and documented instead in each module's own Notes section.
#
# - cpu_usage's real, functioning 'path' option (default '/proc/stat',
#   confirmed in i3status.c's cfg_opt_t usage_opts) is deliberately kept
#   off that module's class body - see cpu_usage.py's post_config_hook()
#   and Notes - so it can't be checked here via getattr(cls, "path") like
#   every other key. Its default is instead verified behaviorally in
#   test_cpu_usage.py (reads real /proc/stat when unset).
#
# - battery's real, functioning 'integer_battery_capacity' option
#   (default False, confirmed in i3status.c's cfg_opt_t battery_opts) is
#   likewise kept off that module's class body - see battery.py's
#   post_config_hook() and Notes - so it can't be checked here either.
#   Its default/behavior is instead verified behaviorally in
#   test_battery.py.


REAL_I3STATUS_DEFAULTS = {
    "run_watch": {"format": "%title: %status", "format_down": None, "pidfile": None},
    "path_exists": {"format": "%title: %status", "format_down": None, "path": None},
    "wireless": {
        "format_up": "W: (%quality at %essid, %bitrate) %ip",
        "format_down": "W: down",
        "format_bitrate": "%g %cb/s",
        "format_noise": "%3d%s",
        "format_quality": "%3d%s",
        "format_signal": "%3d%s",
    },
    "ethernet": {"format_up": "E: %ip (%speed)", "format_down": "E: down"},
    "ipv6": {"format_up": "%ip", "format_down": "no IPv6"},
    "battery": {
        "format": "%status %percentage %remaining",
        "format_down": "No battery",
        "format_percentage": "%.02f%s",
        "status_chr": "CHR",
        "status_bat": "BAT",
        "status_unk": "UNK",
        "status_full": "FULL",
        "status_idle": "IDLE",
        "path": "/sys/class/power_supply/BAT%d/uevent",
        "low_threshold": 30,
        "threshold_type": "time",
        "last_full_capacity": False,
        "hide_seconds": True,
    },
    "time": {"format": "%Y-%m-%d %H:%M:%S"},
    "tztime": {
        "format": "%Y-%m-%d %H:%M:%S %Z",
        "timezone": "",
        "locale": "",
        "format_time": None,
        "hide_if_equals_localtime": False,
    },
    "ddate": {"format": "%{%a, %b %d%}, %Y%N - %H"},
    "load": {"format": "%1min %5min %15min", "format_above_threshold": None, "max_threshold": 5},
    "memory": {
        "format": "%used %free %available",
        "format_degraded": None,
        "threshold_degraded": None,
        "threshold_critical": None,
        "memory_used_method": "classical",
        "unit": "auto",
        "decimals": 1,
    },
    "cpu_usage": {
        "format": "%usage",
        "format_above_threshold": None,
        "format_above_degraded_threshold": None,
        "max_threshold": 95,
        "degraded_threshold": 90,
    },
    "cpu_temperature": {
        "format": "%degrees C",
        "format_above_threshold": None,
        "max_threshold": 75,
    },
    "disk": {
        "format": "%free",
        "format_below_threshold": None,
        "prefix_type": "binary",
        "threshold_type": "percentage_avail",
        "low_threshold": 0,
    },
    "volume": {
        "format": "♪: %volume",
        "format_muted": "♪: 0%%",
        "device": "default",
        "mixer": "Master",
        "mixer_idx": 0,
    },
    "read_file": {
        "format": "%content",
        "format_bad": "%title - %errno: %error",
        "path": None,
        "max_characters": 255,
    },
}


def _module_class(module_name):
    import importlib

    module = importlib.import_module(f"py3status.i3status.modules.{module_name}")
    return module.Py3status


@pytest.mark.parametrize(
    ("module_name", "key", "expected"),
    [
        (module_name, key, expected)
        for module_name, keys in REAL_I3STATUS_DEFAULTS.items()
        for key, expected in keys.items()
    ],
)
def test_default_matches_real_i3status(module_name, key, expected):
    cls = _module_class(module_name)
    assert getattr(cls, key) == expected
