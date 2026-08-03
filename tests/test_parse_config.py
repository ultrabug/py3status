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
