"""Tests for the battery i3status-compatible module."""

BATTERY_UEVENT_NOT_CHARGING = """POWER_SUPPLY_STATUS=Not charging
POWER_SUPPLY_VOLTAGE_NOW=14888000
POWER_SUPPLY_POWER_NOW=0
POWER_SUPPLY_ENERGY_FULL_DESIGN=52500000
POWER_SUPPLY_ENERGY_FULL=50990000
POWER_SUPPLY_ENERGY_NOW=9430000
POWER_SUPPLY_CAPACITY=18
"""


BATTERY_UEVENT_DISCHARGING = """POWER_SUPPLY_STATUS=Discharging
POWER_SUPPLY_VOLTAGE_NOW=14888000
POWER_SUPPLY_CURRENT_NOW=1000000
POWER_SUPPLY_ENERGY_FULL_DESIGN=52500000
POWER_SUPPLY_ENERGY_FULL=50990000
POWER_SUPPLY_ENERGY_NOW=9430000
POWER_SUPPLY_CAPACITY=18
"""


def test_battery_real_hardware_uevent_matches_i3status(make_module, tmp_path):
    # this exact uevent content was captured from this machine's real BAT0
    # and cross-checked byte-for-byte against the real i3status binary:
    # "IDLE 17.96%   0.00W"
    from py3status.i3status.modules.battery import Py3status as Battery

    (tmp_path / "uevent0").write_text(BATTERY_UEVENT_NOT_CHARGING)
    module = make_module(
        Battery,
        path=str(tmp_path / "uevent%d"),
        number=0,
        format="%status %percentage %remaining %emptytime %consumption",
    )
    module.post_config_hook()

    result = module.battery()

    assert result["full_text"] == "IDLE 17.96%   0.00W"


def test_battery_discharging_below_time_threshold_colors_bad(make_module, tmp_path):
    from py3status.i3status.modules.battery import Py3status as Battery

    (tmp_path / "uevent0").write_text(BATTERY_UEVENT_DISCHARGING)
    module = make_module(
        Battery,
        path=str(tmp_path / "uevent%d"),
        number=0,
        low_threshold=999999,
        threshold_type="time",
    )
    module.py3.COLOR_BAD = "#FF0000"
    module.post_config_hook()

    result = module.battery()

    assert result["color"] == "#FF0000"
    assert result["full_text"].startswith("BAT")


def test_battery_down_when_path_missing(make_module, tmp_path):
    from py3status.i3status.modules.battery import Py3status as Battery

    module = make_module(
        Battery,
        path=str(tmp_path / "nonexistent%d"),
        number=5,
        format_down="NO BATTERY HERE",
    )
    module.post_config_hook()

    result = module.battery()

    assert result["full_text"] == "NO BATTERY HERE"


def test_battery_all_aggregates_multiple_batteries(make_module, tmp_path):
    from py3status.i3status.modules.battery import Py3status as Battery

    (tmp_path / "uevent0").write_text(BATTERY_UEVENT_NOT_CHARGING)
    module = make_module(Battery, path=str(tmp_path / "uevent%d"), number="all", format="%status")
    module.post_config_hook()

    result = module.battery()

    assert result["full_text"] == "IDLE"


def test_battery_integer_battery_capacity_overrides_default_format_percentage(make_module):
    # matches real i3status exactly (i3status.c): only takes effect while
    # format_percentage is still the literal default string
    from py3status.i3status.modules.battery import Py3status as Battery

    module = make_module(Battery, integer_battery_capacity=True)
    module.post_config_hook()

    assert module.format_percentage == "%.00f%s"
    module.py3.log.assert_not_called()


def test_battery_integer_battery_capacity_is_noop_when_format_percentage_customized(make_module):
    # matches real i3status exactly: a customized format_percentage means
    # integer_battery_capacity is deprecated/ignored, with a warning logged
    # instead of silently overriding the user's own format
    from py3status.i3status.modules.battery import Py3status as Battery

    module = make_module(Battery, integer_battery_capacity=True, format_percentage="%.01f%s")
    module.post_config_hook()

    assert module.format_percentage == "%.01f%s"
    module.py3.log.assert_called_once_with(
        "battery: integer_battery_capacity is deprecated",
        level=module.py3.LOG_WARNING,
    )
