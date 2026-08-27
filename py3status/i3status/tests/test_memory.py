"""Tests for the memory i3status-compatible module."""

FAKE_MEMINFO = """MemTotal:       61335600 kB
MemFree:        32463420 kB
MemAvailable:   54205932 kB
Buffers:            3704 kB
Cached:         21069672 kB
Shmem:            159768 kB
Other:                 0 kB
"""


def test_memory_default_format(make_module, monkeypatch):
    from py3status.i3status.modules.memory import Py3status as Memory

    module = make_module(Memory)
    monkeypatch.setattr(
        module,
        "_read_meminfo",
        lambda: {
            "total": 61335600 * 1024,
            "free": 32463420 * 1024,
            "available": 54205932 * 1024,
            "buffers": 3704 * 1024,
            "cached": 21069672 * 1024,
            "shared": 159768 * 1024,
        },
    )
    module.post_config_hook()

    result = module.memory()

    assert result["full_text"] == "7.4 GiB 31.0 GiB 51.7 GiB"
    assert "color" not in result


def test_memory_threshold_critical_colors_bad_and_uses_format_degraded(make_module, monkeypatch):
    from py3status.i3status.modules.memory import Py3status as Memory

    module = make_module(Memory, threshold_critical="10%", format_degraded="LOW MEMORY")
    monkeypatch.setattr(
        module,
        "_read_meminfo",
        lambda: {
            "total": 1000 * 1024,
            "free": 100 * 1024,
            "available": 50 * 1024,
            "buffers": 0,
            "cached": 0,
            "shared": 0,
        },
    )
    module.post_config_hook()

    result = module.memory()

    assert result["full_text"] == "LOW MEMORY"
    assert result["color"] == "#FF0000"


def test_memory_meminfo_unreadable(make_module, monkeypatch):
    # matches real i3status exactly: /proc/meminfo missing/unreadable
    # outputs "can't read memory" with no color (confirmed in
    # src/print_mem.c)
    from py3status.i3status.modules.memory import Py3status as Memory

    def raise_oserror():
        raise OSError("no such file")

    module = make_module(Memory)
    monkeypatch.setattr(module, "_read_meminfo", raise_oserror)
    module.post_config_hook()

    result = module.memory()

    assert result["full_text"] == "can't read memory"
    assert "color" not in result


def test_memory_meminfo_missing_required_field(make_module, monkeypatch):
    # matches real i3status: a truncated/malformed /proc/meminfo (missing
    # one of the required fields) is treated the same as unreadable
    from py3status.i3status.modules.memory import Py3status as Memory

    module = make_module(Memory)
    monkeypatch.setattr(module, "_read_meminfo", lambda: {"total": 1000, "free": 500})
    module.post_config_hook()

    result = module.memory()

    assert result["full_text"] == "can't read memory"
    assert "color" not in result
