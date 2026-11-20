"""Tests for the run_watch i3status-compatible module."""

import os

import pytest


def test_run_watch_process_running(make_module, tmp_path):
    from py3status.i3status.modules.run_watch import Py3status as RunWatch

    pidfile = tmp_path / "test.pid"
    pidfile.write_text(str(os.getpid()))
    module = make_module(RunWatch, pidfile=str(pidfile), title="test")
    module.py3.COLOR_GOOD = "#00FF00"
    module.post_config_hook()

    result = module.run_watch()

    assert result["full_text"] == "test: yes"
    assert result["color"] == "#00FF00"


def test_run_watch_process_not_running_uses_format_down(make_module, tmp_path):
    from py3status.i3status.modules.run_watch import Py3status as RunWatch

    pidfile = tmp_path / "test.pid"
    pidfile.write_text("999999999")
    module = make_module(RunWatch, pidfile=str(pidfile), title="test", format_down="DEAD")
    module.post_config_hook()

    result = module.run_watch()

    assert result["full_text"] == "DEAD"
    assert result["color"] == "#FF0000"


def test_run_watch_no_pidfile_configured_raises(make_module):
    # real i3status crashes its whole process here (glob(NULL, ...) fails,
    # hitting die("glob() failed") - confirmed via a real, empty
    # `run_watch X { }` section with no pidfile key: exit code 1, that
    # exact stderr message). This module raises instead of taking the
    # whole bar down with it - py3status disables just this module and
    # shows the error itself.
    from py3status.i3status.modules.run_watch import Py3status as RunWatch

    module = make_module(RunWatch, title="test")

    with pytest.raises(Exception, match="missing pidfile"):
        module.post_config_hook()


def test_run_watch_glob_stops_at_first_unreadable_match(make_module, tmp_path):
    # matches i3status: gives up at the first unreadable glob match rather
    # than trying the rest, even if a later one would succeed
    from py3status.i3status.modules.run_watch import Py3status as RunWatch

    (tmp_path / "a.pid").write_text("not-a-number")
    (tmp_path / "b.pid").write_text(str(os.getpid()))
    module = make_module(RunWatch, pidfile=str(tmp_path / "*.pid"), title="test")
    module.post_config_hook()

    result = module.run_watch()

    assert result["full_text"] == "test: no"
    assert result["color"] == "#FF0000"


def test_run_watch_no_title_configured_raises(make_module, tmp_path):
    # real i3status always has a title here (it comes from the section
    # syntax itself, eg `run_watch VPN { }`), so there's no equivalent
    # "unconfigured title" case to match - this module simply requires
    # title to be set explicitly, same as pidfile.
    from py3status.i3status.modules.run_watch import Py3status as RunWatch

    pidfile = tmp_path / "test.pid"
    pidfile.write_text(str(os.getpid()))
    module = make_module(RunWatch, pidfile=str(pidfile))

    with pytest.raises(Exception, match="missing title"):
        module.post_config_hook()


def test_run_watch_no_title_or_pidfile_configured_raises_combined(make_module):
    from py3status.i3status.modules.run_watch import Py3status as RunWatch

    module = make_module(RunWatch)

    with pytest.raises(Exception, match="missing title, pidfile"):
        module.post_config_hook()
