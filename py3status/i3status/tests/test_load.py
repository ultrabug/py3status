"""Tests for the load i3status-compatible module."""

from py3status.i3status.modules.load import Py3status as Load


def test_load_default_format(make_module, monkeypatch):
    module = make_module(Load)
    monkeypatch.setattr("os.getloadavg", lambda: (0.46, 0.62, 0.59))

    result = module.load()

    assert result["full_text"] == "0.46 0.62 0.59"
    assert "color" not in result


def test_load_above_threshold_uses_format_above_threshold(make_module, monkeypatch):
    module = make_module(Load, max_threshold=-1, format_above_threshold="ABOVE")
    monkeypatch.setattr("os.getloadavg", lambda: (0.46, 0.62, 0.59))

    result = module.load()

    assert result["full_text"] == "ABOVE"
    assert result["color"] == "#FF0000"


def test_load_above_threshold_without_format_above_threshold_keeps_format(make_module, monkeypatch):
    module = make_module(Load, max_threshold=-1)
    monkeypatch.setattr("os.getloadavg", lambda: (0.46, 0.62, 0.59))

    result = module.load()

    assert result["full_text"] == "0.46 0.62 0.59"
    assert result["color"] == "#FF0000"


def test_load_getloadavg_fails(make_module, monkeypatch):
    # matches real i3status exactly: getloadavg() failure outputs
    # "cant read load" with no color (confirmed in src/print_load.c)
    module = make_module(Load)

    def raise_oserror():
        raise OSError("no such thing")

    monkeypatch.setattr("os.getloadavg", raise_oserror)

    result = module.load()

    assert result["full_text"] == "cant read load"
    assert "color" not in result
