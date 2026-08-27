"""Tests for the cpu_usage i3status-compatible module."""


def fake_proc_stat(cpu_lines):
    """cpu_lines: dict of cpu_index -> (user, nice, system, idle)."""
    lines = ["cpu  0 0 0 0 0 0 0 0 0 0\n"]
    for idx in sorted(cpu_lines):
        user, nice, system, idle = cpu_lines[idx]
        lines.append(f"cpu{idx} {user} {nice} {system} {idle} 0 0 0 0 0 0\n")
    return "".join(lines)


def test_cpu_usage_first_call_is_average_since_boot(make_module, tmp_path):
    from py3status.i3status.modules.cpu_usage import Py3status as CpuUsage

    stat_file = tmp_path / "stat"
    # total=150+850=1000, idle=850 -> 15% average usage since boot
    stat_file.write_text(fake_proc_stat({0: (150, 0, 0, 850)}))

    module = make_module(CpuUsage, path=str(stat_file), format="%usage %cpu0")
    module.post_config_hook()

    result = module.cpu_usage()

    assert result["full_text"] == "15% 15%"


def test_cpu_usage_second_call_uses_delta_since_previous_call(make_module, tmp_path):
    from py3status.i3status.modules.cpu_usage import Py3status as CpuUsage

    stat_file = tmp_path / "stat"
    stat_file.write_text(fake_proc_stat({0: (500, 0, 350, 850)}))

    module = make_module(CpuUsage, path=str(stat_file), format="%usage")
    module.post_config_hook()
    module.cpu_usage()  # first call establishes the baseline

    # advance by total=100, idle=50 -> 50% busy over this interval
    stat_file.write_text(fake_proc_stat({0: (525, 0, 375, 900)}))
    result = module.cpu_usage()

    assert result["full_text"] == "50%"


def test_cpu_usage_above_threshold_colors_bad(make_module, tmp_path):
    from py3status.i3status.modules.cpu_usage import Py3status as CpuUsage

    stat_file = tmp_path / "stat"
    stat_file.write_text(fake_proc_stat({0: (1000, 0, 0, 0)}))

    module = make_module(CpuUsage, path=str(stat_file), max_threshold=50)
    module.post_config_hook()

    result = module.cpu_usage()

    assert result["full_text"] == "100%"
    assert result["color"] == "#FF0000"


def test_cpu_usage_path_defaults_to_real_proc_stat_when_unset(make_module):
    # 'path' is a real, undocumented i3status option (see module Notes) -
    # deliberately kept off the class body, so this confirms the fallback
    # in post_config_hook() still resolves to the real default when a
    # user hasn't set it, rather than raising AttributeError
    from py3status.i3status.modules.cpu_usage import Py3status as CpuUsage

    module = make_module(CpuUsage)
    module.post_config_hook()

    assert module.path == "/proc/stat"


def test_cpu_usage_path_unreadable(make_module, tmp_path):
    # matches real i3status exactly: an unreadable path outputs
    # "cant read cpu usage" with no color (confirmed in
    # src/print_cpu_usage.c)
    from py3status.i3status.modules.cpu_usage import Py3status as CpuUsage

    module = make_module(CpuUsage, path=str(tmp_path / "missing"))
    module.post_config_hook()

    result = module.cpu_usage()

    assert result["full_text"] == "cant read cpu usage"
    assert "color" not in result
