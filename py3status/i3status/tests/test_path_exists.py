"""Tests for the path_exists i3status-compatible module."""

import pytest


def test_path_exists_true(make_module, tmp_path):
    from py3status.i3status.modules.path_exists import Py3status as PathExists

    existing = tmp_path / "here"
    existing.write_text("")
    module = make_module(PathExists, path=str(existing), title="test")
    module.py3.COLOR_GOOD = "#00FF00"

    result = module.path_exists()

    assert result["full_text"] == "test: yes"
    assert result["color"] == "#00FF00"


def test_path_exists_false_uses_format_down(make_module, tmp_path):
    from py3status.i3status.modules.path_exists import Py3status as PathExists

    module = make_module(
        PathExists,
        path=str(tmp_path / "missing"),
        title="test",
        format_down="MISSING: %title",
    )

    result = module.path_exists()

    assert result["full_text"] == "MISSING: test"
    assert result["color"] == "#FF0000"


def test_path_exists_no_path_configured_raises(make_module):
    # real i3status prints "X: no" here with no color at all (confirmed
    # via a real, empty `path_exists X { }` section with no path key).
    # This module raises instead, since path has no sane default -
    # py3status disables the module and shows the error itself.
    from py3status.i3status.modules.path_exists import Py3status as PathExists

    module = make_module(PathExists, title="X")

    with pytest.raises(Exception, match="missing path"):
        module.post_config_hook()


def test_path_exists_no_title_configured_raises(make_module, tmp_path):
    # real i3status always has a title here (it comes from the section
    # syntax itself, eg `path_exists VPN { }`), so there's no equivalent
    # "unconfigured title" case to match - this module simply requires
    # title to be set explicitly, same as path.
    from py3status.i3status.modules.path_exists import Py3status as PathExists

    module = make_module(PathExists, path=str(tmp_path / "here"))

    with pytest.raises(Exception, match="missing title"):
        module.post_config_hook()


def test_path_exists_no_title_or_path_configured_raises_combined(make_module):
    from py3status.i3status.modules.path_exists import Py3status as PathExists

    module = make_module(PathExists)

    with pytest.raises(Exception, match="missing title, path"):
        module.post_config_hook()
