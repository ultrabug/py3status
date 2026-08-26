"""Tests for the time i3status-compatible module."""


def test_time_default_format(make_module, monkeypatch):
    from py3status.i3status.modules.time import Py3status as Time

    class FakeDatetime:
        @staticmethod
        def now():
            import datetime as real_datetime

            return real_datetime.datetime(2026, 8, 26, 8, 58, 20)

    monkeypatch.setattr("py3status.i3status.modules.time.datetime", FakeDatetime)
    module = make_module(Time)

    result = module.time()

    assert result["full_text"] == "2026-08-26 08:58:20"
