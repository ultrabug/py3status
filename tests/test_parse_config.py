from codecs import BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE

import pytest

import py3status.parse_config as parse_config

CONFIG = '''\
order += "static_string"
static_string {
    format = "café"
}
'''

DETECTED_CONFIGS = [
    (CONFIG.encode("latin-1"), b"iso-8859-1"),
    (BOM_UTF16_LE + CONFIG.encode("utf-16-le"), b"utf-16le"),
    (BOM_UTF16_BE + CONFIG.encode("utf-16-be"), b"utf-16be"),
    (BOM_UTF32_LE + CONFIG.encode("utf-32-le"), b"utf-32le"),
    (BOM_UTF32_BE + CONFIG.encode("utf-32-be"), b"utf-32be"),
]


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (CONFIG.replace("café", "cafe").encode("ascii"), "cafe"),
        (CONFIG.encode("utf-8"), "café"),
        (CONFIG.encode("utf-8-sig"), "café"),
    ],
)
def test_process_config_without_detection(tmp_path, monkeypatch, payload, expected):
    def unexpected_file_call(*args, **kwargs):
        raise AssertionError("file should not be called for ASCII or UTF-8 config")

    monkeypatch.setattr(parse_config, "check_output", unexpected_file_call)
    config_path = tmp_path / "py3status.conf"
    config_path.write_bytes(payload)

    config = parse_config.process_config(config_path)

    assert config["static_string"]["format"] == expected


@pytest.mark.parametrize(
    ("payload", "detected_encoding"),
    DETECTED_CONFIGS,
)
def test_process_config_detected_encoding(tmp_path, monkeypatch, payload, detected_encoding):
    def detect_encoding(command, timeout):
        assert command[:4] == ["file", "-b", "--mime-encoding", "--dereference"]
        assert timeout == 3
        return detected_encoding

    monkeypatch.setattr(parse_config, "check_output", detect_encoding)
    config_path = tmp_path / "py3status.conf"
    config_path.write_bytes(payload)

    config = parse_config.process_config(config_path)

    assert config["static_string"]["format"] == "café"


@pytest.mark.parametrize("payload", [payload for payload, _ in DETECTED_CONFIGS])
def test_process_config_file_detection(tmp_path, payload):
    config_path = tmp_path / "py3status.conf"
    config_path.write_bytes(payload)

    config = parse_config.process_config(config_path)

    assert config["static_string"]["format"] == "café"


I3S_ORDER_CONFIG = '''\
order += "battery"
order += "disk /"
order += "load"
'''


def test_i3status_names_delegate_to_i3status_by_default(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text(I3S_ORDER_CONFIG)

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["battery", "disk /", "load"]
    assert config["py3_modules"] == []


def test_python_true_in_module_section_resolves_to_py3status(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text(I3S_ORDER_CONFIG + '''
battery {
    python = True
}
''')

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["disk /", "load"]
    assert config["py3_modules"] == ["battery"]


def test_python_key_is_stripped_from_module_config(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "battery"
battery {
    python = True
    format = "CUSTOM"
    low_threshold = 20
}
''')

    config = parse_config.process_config(config_path)

    assert config["battery"] == {"format": "CUSTOM", "low_threshold": 20}


def test_python_false_behaves_like_unset(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "battery"
battery {
    python = False
}
''')

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["battery"]
    assert config["py3_modules"] == []


def test_python_true_translates_instance_into_config(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "disk /home"
order += "battery 0"
order += "ethernet eth0"

disk "/home" {
    python = True
}
battery 0 {
    python = True
}
ethernet eth0 {
    python = True
}
''')

    config = parse_config.process_config(config_path)

    assert config["disk /home"] == {"path": "/home"}
    assert config["battery 0"] == {"number": "0"}
    assert config["ethernet eth0"] == {"interface": "eth0"}


def test_python_true_translated_instance_does_not_override_explicit_config(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "disk /home"
disk "/home" {
    python = True
    path = "/custom"
}
''')

    config = parse_config.process_config(config_path)

    assert config["disk /home"] == {"path": "/custom"}


def test_python_directive_scoped_to_i3status_module_names_only(tmp_path):
    # a non-i3status module's own "python" config key (should it ever
    # have one) is left alone entirely - not consulted for dispatch, not
    # stripped, and no instance translation is attempted against it
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "some_custom_module"
some_custom_module {
    python = True
    format = "hi"
}
''')

    config = parse_config.process_config(config_path)

    assert config["py3_modules"] == ["some_custom_module"]
    assert config["some_custom_module"] == {"python": True, "format": "hi"}


def test_wrapper_delegated_module_strips_its_instance_only_config_key(tmp_path):
    # a leftover title/path/zone/interface/number key (eg left behind
    # after removing python = True, or just copy-pasted) is not a real
    # i3status config option for these modules - real i3status hard-
    # errors ("no such option") parsing it, taking the whole wrapper
    # subprocess down, not just this module. Confirmed against the real
    # binary: i3status_diff.py 'order += "run_watch VPN"\n\nrun_watch VPN {\n
    # title = "VPN"\n pidfile = "x"\n}' -> exit code 1, "no such option 'title'"
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "run_watch VPN"
order += "disk /home"

run_watch VPN {
    title = "VPN"
    pidfile = "/nonexistent"
}
disk "/home" {
    path = "/home"
}
''')

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["run_watch VPN", "disk /home"]
    assert config["run_watch VPN"] == {"pidfile": "/nonexistent"}
    assert config["disk /home"] == {}


def test_wrapper_delegated_module_keeps_keys_that_are_genuinely_valid(tmp_path):
    # unlike disk's 'path', read_file/path_exists genuinely do have a
    # real 'path' config option in real i3status - must not be stripped
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "read_file UPTIME"
read_file UPTIME {
    path = "/proc/uptime"
}
''')

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["read_file UPTIME"]
    assert config["read_file UPTIME"] == {"path": "/proc/uptime"}


def test_python_true_module_keeps_its_instance_only_config_key(tmp_path):
    # the same key that must be stripped for wrapper delegation is
    # exactly what's needed (and expected) when resolving natively
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "run_watch VPN"
run_watch VPN {
    python = True
    title = "VPN"
    pidfile = "/nonexistent"
}
''')

    config = parse_config.process_config(config_path)

    assert config["py3_modules"] == ["run_watch VPN"]
    assert config["run_watch VPN"] == {"title": "VPN", "pidfile": "/nonexistent"}


def test_wrapper_delegated_module_strips_cache_timeout(tmp_path):
    # cache_timeout is a py3status-only per-module override of real
    # i3status's single general.interval - never a real i3status config
    # option on ANY module, unlike eg disk's 'path' which is tied to just
    # that one module. Confirmed against the real binary: a leftover
    # cache_timeout crashes the wrapper with "no such option" exactly
    # like a leftover instance-only key would.
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "load"
load {
    cache_timeout = 5
    format = "CUSTOM"
}
''')

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["load"]
    assert config["load"] == {"format": "CUSTOM"}


def test_python_true_module_keeps_cache_timeout(tmp_path):
    # the same key that must be stripped for wrapper delegation is
    # exactly what's needed (and expected) when resolving natively
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
order += "load"
load {
    python = True
    cache_timeout = 5
}
''')

    config = parse_config.process_config(config_path)

    assert config["py3_modules"] == ["load"]
    assert config["load"] == {"cache_timeout": 5}


def test_i3status_python_global_default_resolves_all_i3status_names_natively(tmp_path):
    # py3status { i3status = "python" } applies to every real i3status
    # module name at once, with no explicit config block needed at all
    # - the section's own instance is still auto-translated correctly
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
py3status {
    i3status = "python"
}

order += "battery 0"
order += "disk /home"
''')

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == []
    assert config["py3_modules"] == ["battery 0", "disk /home"]
    assert config["battery 0"] == {"number": "0"}
    assert config["disk /home"] == {"path": "/home"}


def test_i3status_python_global_default_overridden_by_explicit_python_false(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
py3status {
    i3status = "python"
}

order += "battery 0"
order += "wireless wlan0"

wireless wlan0 {
    python = False
}
''')

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["wireless wlan0"]
    assert config["py3_modules"] == ["battery 0"]
    # the invalid-for-real-i3status "python" key must not leak through
    # to the wrapper even when explicitly set to False
    assert config["wireless wlan0"] == {}


def test_i3status_python_global_default_overridden_by_explicit_python_true(tmp_path):
    # explicit python = True still works the same whether or not a
    # global default is set
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
py3status {
    i3status = "python"
}

order += "load"
order += "battery 0"

battery 0 {
    python = True
    number = 1
}
''')

    config = parse_config.process_config(config_path)

    assert config["py3_modules"] == ["load", "battery 0"]
    # explicit number=1 wins over the "0" translate_instance would imply
    assert config["battery 0"] == {"number": 1}


def test_i3status_python_global_default_unset_keeps_todays_default(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text(I3S_ORDER_CONFIG)

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["battery", "disk /", "load"]
    assert config["py3_modules"] == []


def test_i3status_python_global_default_ignores_other_values(tmp_path):
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
py3status {
    i3status = "rust"
}

order += "battery"
''')

    config = parse_config.process_config(config_path)

    assert config["i3s_modules"] == ["battery"]
    assert config["py3_modules"] == []


def test_i3s_py_modules_only_lists_natively_resolved_i3status_names(tmp_path):
    # i3s_py_modules is a subset of py3_modules: only entries whose
    # name is one of the 16 real i3status module names AND resolved
    # natively - an ordinary py3status module (not an i3status name at all)
    # must not show up here even though it's also in py3_modules
    config_path = tmp_path / "py3status.conf"
    config_path.write_text('''\
py3status {
    i3status = "python"
}

order += "battery 0"
order += "static_string"
order += "wireless wlan0"

wireless wlan0 {
    python = False
}
''')

    config = parse_config.process_config(config_path)

    assert config["py3_modules"] == ["battery 0", "static_string"]
    assert config["i3s_py_modules"] == ["battery 0"]
