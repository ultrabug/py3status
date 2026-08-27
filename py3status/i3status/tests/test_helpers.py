"""Tests for shared i3status-compatible helpers (py3status/i3status/helpers.py)."""

from unittest.mock import Mock

import pytest

import py3status.i3status.helpers as helpers_module

format_placeholders = helpers_module.format_placeholders
translate_instance = helpers_module.translate_instance


def test_format_placeholders_prefers_longer_overlapping_name_first():
    # %percentage_used is a prefix of %percentage_used_of_avail; the more
    # specific name must be listed (and therefore matched) first
    placeholders = [
        ("%percentage_used_of_avail", "AVAIL"),
        ("%percentage_used", "USED"),
    ]
    assert (
        format_placeholders("%percentage_used_of_avail and %percentage_used", placeholders)
        == "AVAIL and USED"
    )


def test_resolve_cache_timeout_prefers_explicit_module_setting():
    py3 = Mock()
    py3._get_config_setting = Mock(return_value=7)

    assert helpers_module.resolve_cache_timeout(py3, 3) == 3
    py3._get_config_setting.assert_not_called()


def test_resolve_cache_timeout_falls_back_to_general_interval():
    py3 = Mock()
    py3._get_config_setting = Mock(return_value=7)

    assert helpers_module.resolve_cache_timeout(py3, None) == 7
    py3._get_config_setting.assert_called_once_with("interval", 1)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("disk /home", {"path": "/home"}),
        ("disk /", {"path": "/"}),
        ("cpu_temperature 0", {"zone": 0}),
        ("cpu_temperature 2", {"zone": 2}),
        ("ethernet eth0", {"interface": "eth0"}),
        ("ethernet _first_", {"interface": "_first_"}),
        ("wireless wlan0", {"interface": "wlan0"}),
        ("wireless _first_", {"interface": "_first_"}),
        ("battery 0", {"number": "0"}),
        ("battery all", {"number": "all"}),
        ("battery ALL", {"number": "ALL"}),
        ("run_watch VPN", {"title": "VPN"}),
        ("path_exists VPN", {"title": "VPN"}),
        ("read_file UPTIME", {"title": "UPTIME"}),
    ],
)
def test_translate_instance(name, expected):
    assert translate_instance(name) == expected


def test_translate_instance_cpu_temperature_non_numeric_falls_back_to_zero():
    # matches real i3status's atoi(title): non-numeric input silently
    # becomes 0 rather than raising
    assert translate_instance("cpu_temperature abc") == {"zone": 0}


@pytest.mark.parametrize(
    "name",
    [
        "load",
        "cpu_usage",
        "ddate",
        "ipv6",
        "time",
        "disk",
        "battery",
        "ethernet",
        "wireless",
        "cpu_temperature",
        "run_watch",
        "path_exists",
        "read_file",
    ],
)
def test_translate_instance_no_instance_given_returns_empty(name):
    assert translate_instance(name) == {}


@pytest.mark.parametrize(
    "name",
    [
        "tztime local",
        "volume master",
    ],
)
def test_translate_instance_title_not_derived_for_these_modules(name):
    # real i3status uses title for these two only as i3bar instance
    # metadata (INSTANCE() macro), never derived into an actual config
    # value - timezone/device/mixer are genuinely separate config keys
    assert translate_instance(name) == {}


def test_translate_instance_unknown_module_returns_empty():
    assert translate_instance("some_third_party_module instance") == {}
