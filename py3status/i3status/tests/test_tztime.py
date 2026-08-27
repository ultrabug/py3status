"""Tests for the tztime i3status-compatible module."""


def test_tztime_uses_given_timezone(make_module):
    import py3status.i3status.modules.tztime as tztime_module

    TzTime = tztime_module.Py3status

    module = make_module(TzTime, timezone="Europe/Berlin", format="%Z")
    module.post_config_hook()

    assert module.tztime()["full_text"] in ("CET", "CEST")


def test_tztime_hide_if_equals_localtime(make_module):
    from datetime import datetime

    import py3status.i3status.modules.tztime as tztime_module

    TzTime = tztime_module.Py3status

    local_tz_name = (
        datetime.now().astimezone().tzinfo.key
        if hasattr(datetime.now().astimezone().tzinfo, "key")
        else None
    )

    module = make_module(TzTime, timezone=local_tz_name or "", hide_if_equals_localtime=True)
    module.post_config_hook()

    assert module.tztime()["full_text"] == ""


def test_tztime_format_time_substitutes_into_format(make_module):
    import py3status.i3status.modules.tztime as tztime_module

    TzTime = tztime_module.Py3status

    module = make_module(
        TzTime,
        timezone="Europe/Berlin",
        format="<b>time:</b> %time",
        format_time="%H:%M",
    )
    module.post_config_hook()

    result = module.tztime()["full_text"]
    assert result.startswith("<b>time:</b> ")
    assert "%time" not in result


def test_tztime_strftime_serializes_locale_calls_under_lock(make_module, monkeypatch):
    # locale.setlocale() is process-global, not thread-local; verify the
    # whole get/set/restore sequence runs inside _locale_lock so
    # concurrent tztime instances can't interleave and observe each
    # other's locale mid-format
    from datetime import datetime

    import py3status.i3status.modules.tztime as tztime_module

    TzTime = tztime_module.Py3status

    events = []

    class FakeLock:
        def __enter__(self):
            events.append("acquire")

        def __exit__(self, *args):
            events.append("release")

    monkeypatch.setattr(tztime_module, "_locale_lock", FakeLock())
    monkeypatch.setattr(
        tztime_module,
        "setlocale",
        lambda *args: events.append("setlocale") or "C",
    )

    module = make_module(TzTime, locale="en_US.UTF-8")
    module.post_config_hook()
    module._strftime("%H:%M", datetime.now())

    assert events == ["acquire", "setlocale", "setlocale", "setlocale", "release"]
