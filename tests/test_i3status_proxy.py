from datetime import datetime, timezone

import pytest

from py3status.composite import Composite
from py3status.i3status import registry
from py3status.i3status.proxy import Py3status
from py3status.py3 import ModuleErrorException


class FakePy3:
    CACHE_FOREVER = -1

    def time_in(self, seconds=None, sync_to=None, offset=0):
        if sync_to is not None:
            return f"cached_until:sync_to:{sync_to}"
        return f"cached_until:{seconds}"

    def error(self, msg, timeout=None):
        raise ModuleErrorException(msg, timeout)

    def composite_create(self, item):
        return Composite(item)

    def safe_format(self, format_module, param_dict, force_composite=False):
        assert force_composite is True
        # mirror the real formatter closely enough for these tests: a
        # Composite placeholder value renders as its own text content
        param_dict = {
            key: value.text() if isinstance(value, Composite) else value
            for key, value in param_dict.items()
        }
        return [{"full_text": format_module.format(**param_dict)}]


def make_module(container="i3status generated", item_name="disk", item_instance="/"):
    module = Py3status()
    module.py3 = FakePy3()
    module._container = container
    module._item_name = item_name
    module._item_instance = item_instance
    module.post_config_hook()
    return module


def test_post_config_hook_requires_container_and_item_name():
    module = Py3status()
    module.py3 = FakePy3()
    module._container = None
    module._item_name = None
    module._item_instance = None

    with pytest.raises(Exception, match="internal proxy module, not for direct configuration"):
        module.post_config_hook()


def test_no_published_data_yet_returns_empty_output():
    module = make_module(container="i3status generated", item_name="nothing", item_instance=None)

    result = module.i3status_proxy()

    assert result["full_text"] == ""
    assert result["cached_until"] == "cached_until:1"


def test_reads_latest_published_data_and_applies_format_module():
    registry.publish(
        "i3status generated",
        ("disk", "/"),
        {"name": "disk", "instance": "/", "full_text": "42%"},
    )
    module = make_module()
    module.format_module = "USED: {output}"

    result = module.i3status_proxy()

    assert result["composite"] == [{"full_text": "USED: 42%"}]


def test_name_and_instance_are_stripped_before_formatting():
    registry.publish(
        "i3status generated",
        ("wireless", "_first_"),
        {"name": "wireless", "instance": "_first_", "full_text": "WIFI"},
    )
    module = make_module(item_name="wireless", item_instance="_first_")

    captured = {}

    def capturing_safe_format(format_module, param_dict, force_composite=False):
        captured.update(param_dict["output"].get_content()[0])
        return []

    module.py3.safe_format = capturing_safe_format
    module.i3status_proxy()

    assert "name" not in captured
    assert "instance" not in captured
    assert captured["full_text"] == "WIFI"


def test_cache_timeout_is_configurable():
    module = make_module(container="i3status generated", item_name="load", item_instance=None)
    module.cache_timeout = 30

    result = module.i3status_proxy()

    assert result["cached_until"] == "cached_until:30"


def test_dead_container_raises_a_real_clickable_error():
    registry.mark_dead("i3status generated", "not installed")
    module = make_module(container="i3status generated", item_name="disk", item_instance="/")

    with pytest.raises(ModuleErrorException) as exc_info:
        module.i3status_proxy()

    assert exc_info.value.msg == "not installed"
    assert exc_info.value.timeout == module.py3.CACHE_FOREVER


def test_tztime_ticks_locally_and_ignores_cache_timeout():
    """
    By default, time/tztime schedule themselves off the format string's
    own granularity (see TimeZoneTicker._time_delta_for()), not
    cache_timeout - translate.py only sets _cache_timeout when the user
    explicitly configured cache_timeout (see
    test_explicit_cache_timeout_overrides_tztime_ticking below); this
    covers the implicit case.
    """
    module = Py3status()
    module.py3 = FakePy3()
    module._container = "i3status generated"
    module._item_name = "tztime"
    module._item_instance = "local"
    module._interval = 5
    module.format = "%H:%M:%S"
    module.cache_timeout = 999999
    module.post_config_hook()

    # must be close to "now" - set_time_zone() computes an hour/minute
    # offset from utcnow(), and datetime.timezone() rejects anything
    # outside +/-24h, so a stale/hardcoded date would fail to parse
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    registry.publish(
        "i3status generated",
        ("tztime", "local"),
        {"name": "tztime", "instance": "local", "full_text": f"{now_utc} UTC"},
    )

    result = module.i3status_proxy()

    # dispatched to _time_proxy(), not the plain registry-passthrough path
    assert "composite" in result
    # scheduled off the format's own granularity (sync_to), regardless of
    # the (deliberately absurd) cache_timeout configured above
    assert result["cached_until"] == "cached_until:sync_to:1"
    # the raw reading's timezone was actually extracted
    assert module._ticker._tz is not None


def test_explicit_cache_timeout_overrides_tztime_ticking():
    """
    A user who explicitly configured cache_timeout on a time/tztime
    module (translate.py stamps _cache_timeout for this) wants that
    rate instead of the format's own granularity - eg show seconds,
    but only refresh every 10s.
    """
    module = Py3status()
    module.py3 = FakePy3()
    module._container = "i3status generated"
    module._item_name = "tztime"
    module._item_instance = "local"
    module._interval = 5
    module._cache_timeout = True
    module.format = "%H:%M:%S"
    module.cache_timeout = 10
    module.post_config_hook()

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    registry.publish(
        "i3status generated",
        ("tztime", "local"),
        {"name": "tztime", "instance": "local", "full_text": f"{now_utc} UTC"},
    )

    result = module.i3status_proxy()

    assert result["cached_until"] == "cached_until:10"
