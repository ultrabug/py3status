"""Tests for the read_file i3status-compatible module."""

import pytest


def test_read_file_success(make_module, tmp_path):
    from py3status.i3status.modules.read_file import Py3status as ReadFile

    f = tmp_path / "content.txt"
    f.write_text("line one\nline two")
    module = make_module(ReadFile, path=str(f), title="MyFile")
    module.py3.COLOR_GOOD = "#00FF00"
    module.post_config_hook()

    result = module.read_file()

    assert result["full_text"] == "line oneline two"
    assert result["color"] == "#00FF00"


def test_read_file_missing_uses_format_bad(make_module, tmp_path):
    from py3status.i3status.modules.read_file import Py3status as ReadFile

    module = make_module(ReadFile, path=str(tmp_path / "missing"), title="MyFile")
    module.post_config_hook()

    result = module.read_file()

    assert result["full_text"] == "MyFile - 2: No such file or directory"
    assert result["color"] == "#FF0000"


def test_read_file_no_path_configured_raises(make_module):
    # real i3status prints "error: path not configured" here with no
    # color at all (confirmed via a real, empty `read_file X { }` section
    # with no path key). This module raises instead, since path has no
    # sane default - py3status disables the module and shows the error
    # itself.
    from py3status.i3status.modules.read_file import Py3status as ReadFile

    module = make_module(ReadFile, title="MyFile")

    with pytest.raises(Exception, match="missing path"):
        module.post_config_hook()


def test_read_file_no_title_configured_raises(make_module, tmp_path):
    # real i3status always has a title here (it comes from the section
    # syntax itself, eg `read_file UPTIME { }`), so there's no equivalent
    # "unconfigured title" case to match - this module simply requires
    # title to be set explicitly, same as path.
    from py3status.i3status.modules.read_file import Py3status as ReadFile

    module = make_module(ReadFile, path=str(tmp_path / "content.txt"))

    with pytest.raises(Exception, match="missing title"):
        module.post_config_hook()


def test_read_file_no_title_or_path_configured_raises_combined(make_module):
    from py3status.i3status.modules.read_file import Py3status as ReadFile

    module = make_module(ReadFile)

    with pytest.raises(Exception, match="missing title, path"):
        module.post_config_hook()
