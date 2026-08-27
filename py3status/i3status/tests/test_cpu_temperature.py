"""Tests for the cpu_temperature i3status-compatible module."""


def test_cpu_temperature_default_format(make_module, tmp_path):
    from py3status.i3status.modules.cpu_temperature import Py3status as CpuTemp

    temp_file = tmp_path / "temp"
    temp_file.write_text("58000\n")
    module = make_module(CpuTemp, path=str(temp_file))
    module.post_config_hook()

    result = module.cpu_temperature()

    assert result["full_text"] == "58 C"
    assert "color" not in result


def test_cpu_temperature_above_threshold_colors_bad(make_module, tmp_path):
    from py3status.i3status.modules.cpu_temperature import Py3status as CpuTemp

    temp_file = tmp_path / "temp"
    temp_file.write_text("90000\n")
    module = make_module(CpuTemp, path=str(temp_file), max_threshold=75)
    module.post_config_hook()

    result = module.cpu_temperature()

    assert result["full_text"] == "90 C"
    assert result["color"] == "#FF0000"


def test_cpu_temperature_invalid_shows_question_mark(make_module, tmp_path):
    from py3status.i3status.modules.cpu_temperature import Py3status as CpuTemp

    temp_file = tmp_path / "temp"
    temp_file.write_text("-1\n")
    module = make_module(CpuTemp, path=str(temp_file))
    module.post_config_hook()

    result = module.cpu_temperature()

    assert result["full_text"] == "? C"


def test_cpu_temperature_unreadable_path(make_module):
    from py3status.i3status.modules.cpu_temperature import Py3status as CpuTemp

    module = make_module(CpuTemp, path="/nonexistent-xyz")
    module.post_config_hook()

    result = module.cpu_temperature()

    assert result["full_text"] == "can't read temp"
