"""Tests for the volume i3status-compatible module."""

import pytest


def test_volume_reads_real_master_mixer():
    # best-effort sanity check against real hardware, cross-checked against
    # the real i3status binary: "♪: 100%" with device=default, mixer=Master
    # (both are the defaults) - skipped rather than failed when this
    # environment has no such ALSA mixer (eg CI, or any machine without a
    # "Master" control)
    import py3status.i3status.modules.volume as volume_module

    module = volume_module.Py3status()
    module._lib = None

    result = module._read_volume("default", "Master", 0)
    if result is None:
        pytest.skip("no real ALSA 'Master' mixer available in this environment")

    volume, muted, devicename = result
    assert 0 <= volume <= 100
    assert isinstance(muted, bool)
    assert devicename == "Master"


def test_volume_reads_real_pulse_default_sink():
    # best-effort sanity check against real hardware, cross-checked against
    # `pactl get-sink-volume @DEFAULT_SINK@`/`get-sink-mute @DEFAULT_SINK@`
    # on a real PipeWire-managed system - skipped rather than failed when
    # this environment has no reachable PulseAudio/PipeWire server (eg CI)
    import py3status.i3status.modules.volume as volume_module

    module = volume_module.Py3status()
    module._pulse_unavailable = False
    module._pulse_lib = None

    result = module._read_pulse_sink(None, None)
    if result is None:
        pytest.skip("no real PulseAudio/PipeWire default sink available in this environment")

    volume, muted, description = result
    assert volume >= 0
    assert isinstance(muted, bool)
    assert isinstance(description, str)


@pytest.mark.parametrize(
    ("device", "expected"),
    [
        ("default", (False, None, None)),
        ("hw:0", (False, None, None)),
        ("pulse", (True, None, None)),
        ("Pulse", (True, None, None)),
        ("pulse:2", (True, 2, None)),
        ("pulse:myname", (True, None, "myname")),
    ],
)
def test_parse_pulse_device(device, expected):
    import py3status.i3status.modules.volume as volume_module

    _parse_pulse_device = volume_module.Py3status._parse_pulse_device

    assert _parse_pulse_device(device) == expected


def test_volume_unmuted(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    module = make_module(Volume)
    monkeypatch.setattr(module, "_read_pulse_sink", lambda *a, **k: None)
    monkeypatch.setattr(module, "_read_volume", lambda device, mixer, idx: (72, False, "Master"))
    module.post_config_hook()

    result = module.volume()

    assert result["full_text"] == "♪: 72%"
    assert "color" not in result


def test_volume_muted_uses_format_muted(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    module = make_module(Volume)
    monkeypatch.setattr(module, "_read_pulse_sink", lambda *a, **k: None)
    monkeypatch.setattr(module, "_read_volume", lambda device, mixer, idx: (72, True, "Master"))
    module.py3.COLOR_DEGRADED = "#FFFF00"
    module.post_config_hook()

    result = module.volume()

    # the raw default format_muted is "0%%"; %% is itself a placeholder
    # (matching i3status) that renders to a single literal '%'
    assert result["full_text"] == "♪: 0%"
    assert result["color"] == "#FFFF00"


def test_volume_custom_format_with_devicename(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    module = make_module(Volume, format="V: %volume (%devicename)")
    monkeypatch.setattr(module, "_read_pulse_sink", lambda *a, **k: None)
    monkeypatch.setattr(module, "_read_volume", lambda device, mixer, idx: (100, False, "Master"))
    module.post_config_hook()

    result = module.volume()

    assert result["full_text"] == "V: 100% (Master)"


def test_volume_mixer_not_found_outputs_empty_string(make_module, monkeypatch):
    # matches i3status: a mixer-open/find failure gives a genuinely empty
    # full_text, bypassing the user's format entirely - not "0%"
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    module = make_module(Volume, format="SHOULD NOT APPEAR")
    monkeypatch.setattr(module, "_read_pulse_sink", lambda *a, **k: None)
    monkeypatch.setattr(module, "_read_volume", lambda device, mixer, idx: None)
    module.post_config_hook()

    result = module.volume()

    assert result["full_text"] == ""


def test_volume_default_device_prefers_pulse_over_alsa(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    module = make_module(Volume, format="P: %volume (%devicename)")
    monkeypatch.setattr(module, "_read_pulse_sink", lambda *a, **k: (55, False, "Speaker"))

    def unexpected_alsa_call(*args, **kwargs):
        raise AssertionError("ALSA should not be tried when PulseAudio succeeds")

    monkeypatch.setattr(module, "_read_volume", unexpected_alsa_call)
    module.post_config_hook()

    result = module.volume()

    assert result["full_text"] == "P: 55% (Speaker)"


def test_volume_default_device_falls_back_to_alsa_when_pulse_unavailable(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    module = make_module(Volume)
    monkeypatch.setattr(module, "_read_pulse_sink", lambda *a, **k: None)
    monkeypatch.setattr(module, "_read_volume", lambda device, mixer, idx: (40, False, "Master"))
    module.post_config_hook()

    result = module.volume()

    assert result["full_text"] == "♪: 40%"


def test_volume_pulse_device_never_falls_back_to_alsa(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    module = make_module(Volume, device="pulse")
    monkeypatch.setattr(module, "_read_pulse_sink", lambda *a, **k: None)

    def unexpected_alsa_call(*args, **kwargs):
        raise AssertionError("a forced pulse device should never fall back to ALSA")

    monkeypatch.setattr(module, "_read_volume", unexpected_alsa_call)
    module.post_config_hook()

    result = module.volume()

    # matches real i3status: a forced "pulse..." device that can't be
    # reached renders as 0%, unmuted, through the normal (non-muted)
    # format - not the empty-string bypass ALSA failures use
    assert result["full_text"] == "♪: 0%"
    assert "color" not in result


def test_volume_pulse_device_by_index(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    seen = {}

    def fake_read_pulse_sink(sink_index, sink_name):
        seen["sink_index"] = sink_index
        seen["sink_name"] = sink_name
        return 30, True, "HDMI"

    module = make_module(Volume, device="pulse:2")
    monkeypatch.setattr(module, "_read_pulse_sink", fake_read_pulse_sink)
    module.py3.COLOR_DEGRADED = "#FFFF00"
    module.post_config_hook()

    result = module.volume()

    assert seen == {"sink_index": 2, "sink_name": None}
    assert result["full_text"] == "♪: 0%"
    assert result["color"] == "#FFFF00"


def test_volume_pulse_device_by_name(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    seen = {}

    def fake_read_pulse_sink(sink_index, sink_name):
        seen["sink_index"] = sink_index
        seen["sink_name"] = sink_name
        return 60, False, "Headphones"

    module = make_module(Volume, device="pulse:analog-output-headphones")
    monkeypatch.setattr(module, "_read_pulse_sink", fake_read_pulse_sink)
    module.post_config_hook()

    result = module.volume()

    assert seen == {"sink_index": None, "sink_name": "analog-output-headphones"}
    assert result["full_text"] == "♪: 60%"


def test_volume_non_pulse_device_never_calls_pulse(make_module, monkeypatch):
    import py3status.i3status.modules.volume as volume_module

    Volume = volume_module.Py3status

    def unexpected_pulse_call(*args, **kwargs):
        raise AssertionError("an explicit ALSA device should never try PulseAudio")

    module = make_module(Volume, device="hw:0")
    monkeypatch.setattr(module, "_read_pulse_sink", unexpected_pulse_call)
    monkeypatch.setattr(module, "_read_volume", lambda device, mixer, idx: (10, False, "Master"))
    module.post_config_hook()

    result = module.volume()

    assert result["full_text"] == "♪: 10%"
