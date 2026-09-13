import pytest

from py3status.i3status.helpers import parse_onclick


def test_parse_onclick_accepts_button_20():
    """
    1-20 inclusive, matching i3bar's own supported button range and
    parse_config.py's process_onclick() - 20 is a valid button, not an
    off-by-one edge case to reject.
    """
    module = {"on_click 20": "exec echo clicked"}

    clicks = parse_onclick(module, "load")

    assert clicks == {20: "exec echo clicked"}
    assert "on_click 20" not in module


def test_parse_onclick_rejects_button_above_20():
    module = {"on_click 21": "exec echo clicked"}

    with pytest.raises(Exception, match="not in range 1-20"):
        parse_onclick(module, "load")


def test_parse_onclick_rejects_button_below_1():
    module = {"on_click 0": "exec echo clicked"}

    with pytest.raises(Exception, match="not in range 1-20"):
        parse_onclick(module, "load")


def test_parse_onclick_rejects_non_numeric_button():
    module = {"on_click x": "exec echo clicked"}

    with pytest.raises(Exception, match="invalid 'on_click x'"):
        parse_onclick(module, "load")


def test_parse_onclick_rejects_missing_button():
    module = {"on_click": "exec echo clicked"}

    with pytest.raises(Exception, match="invalid 'on_click'"):
        parse_onclick(module, "load")


def test_parse_onclick_returns_none_when_no_clicks_configured():
    module = {"format": "%1min"}

    assert parse_onclick(module, "load") is None


def test_parse_onclick_error_uses_given_name_not_a_module_key():
    """
    A bare i3status item's raw dict never carries its own "name" key (that
    only exists after _flatten_container_items() stamps a configured
    container's items) - the error message must come from the name passed
    in, not module["name"], or this crashes with KeyError instead of the
    intended validation message.
    """
    module = {"on_click 99": "exec echo clicked"}

    with pytest.raises(Exception, match="module 'load': "):
        parse_onclick(module, "load")
