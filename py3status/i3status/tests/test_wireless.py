"""Tests for the wireless i3status-compatible module."""


def test_wireless_nla_pack_parse_roundtrip():
    import py3status.i3status.modules.wireless as wireless_module

    _nla_pack = wireless_module.Py3status._nla_pack
    _nla_parse = wireless_module.Py3status._nla_parse

    packed = _nla_pack(1, b"hello") + _nla_pack(2, struct_pack_u32(42))
    attrs = _nla_parse(packed)

    assert attrs[1] == b"hello"
    assert attrs[2] == struct_pack_u32(42)


def struct_pack_u32(value):
    import struct

    return struct.pack("=I", value)


def test_wireless_find_ssid():
    import py3status.i3status.modules.wireless as wireless_module

    _find_ssid = wireless_module.Py3status._find_ssid

    # IE: eid=0 (SSID), len=8, "TestWifi"
    ies = bytes([0, 8]) + b"TestWifi" + bytes([1, 2, 0xFF, 0xFF])
    assert _find_ssid(ies) == b"TestWifi"


def test_wireless_find_ssid_skips_other_elements_first():
    import py3status.i3status.modules.wireless as wireless_module

    _find_ssid = wireless_module.Py3status._find_ssid

    # IE: eid=1 (not SSID), len=2, then eid=0 (SSID), len=4, "Home"
    ies = bytes([1, 2, 0xAA, 0xBB]) + bytes([0, 4]) + b"Home"
    assert _find_ssid(ies) == b"Home"


def test_wireless_xbm_to_percent_clamps_to_range():
    import py3status.i3status.modules.wireless as wireless_module

    _xbm_to_percent = wireless_module.Py3status._xbm_to_percent

    # -6500 mbm / 100 = -65 dBm; 100 - 70*((-20)-(-65))/((-20)-(-90)) = 55
    assert _xbm_to_percent(-6500, 100) == 55
    # very strong signal clamps to SIGNAL_MAX_DBM (-20) -> 100%
    assert _xbm_to_percent(-1000, 100) == 100
    # very weak signal clamps to NOISE_FLOOR_DBM (-90); the formula bottoms
    # out at 30%, not 0%, by design (inherited from NetworkManager)
    assert _xbm_to_percent(-20000, 100) == 30


def test_wireless_print_bitrate_scales_to_gigabit():
    import py3status.i3status.modules.wireless as wireless_module

    _print_bitrate = wireless_module.Py3status._print_bitrate

    assert _print_bitrate(1225000000, "%g %cb/s") == "1.225 Gb/s"


def test_wireless_print_bitrate_scales_to_megabit():
    import py3status.i3status.modules.wireless as wireless_module

    _print_bitrate = wireless_module.Py3status._print_bitrate

    assert _print_bitrate(54000000, "%g %cb/s") == "54 Mb/s"


def test_wireless_down_when_no_ip(make_module, monkeypatch):
    import py3status.i3status.modules.wireless as wireless_module

    Wireless = wireless_module.Py3status

    monkeypatch.setattr(wireless_module, "get_ipv4_address", lambda i: None)
    monkeypatch.setattr(wireless_module, "get_ipv6_address", lambda i: None)
    module = make_module(Wireless, interface="wlan0")
    module.post_config_hook()

    result = module.wireless()

    assert result["full_text"] == "W: down"
    assert result["color"] == "#FF0000"


def test_wireless_up_with_full_info(make_module, monkeypatch):
    import py3status.i3status.modules.wireless as wireless_module

    Wireless = wireless_module.Py3status

    monkeypatch.setattr(wireless_module, "get_ipv4_address", lambda i: "192.168.1.5")
    monkeypatch.setattr(wireless_module, "get_ipv6_address", lambda i: None)
    module = make_module(Wireless, interface="wlan0")
    monkeypatch.setattr(
        module,
        "_get_wireless_info",
        lambda i: {
            "quality": 66,
            "signal": -65,
            "essid": "Frederick 5G",
            "frequency": 5.18e9,
            "bitrate": 1225000000,
        },
    )
    module.py3.COLOR_GOOD = "#00FF00"
    module.post_config_hook()

    result = module.wireless()

    assert result["full_text"] == "W: ( 66% at Frederick 5G, 1.225 Gb/s) 192.168.1.5"
    assert result["color"] == "#00FF00"


def test_wireless_up_but_no_scan_info_uses_format_down(make_module, monkeypatch):
    # eg interface has an IP but nl80211 couldn't find an associated BSS
    import py3status.i3status.modules.wireless as wireless_module

    Wireless = wireless_module.Py3status

    monkeypatch.setattr(wireless_module, "get_ipv4_address", lambda i: "192.168.1.5")
    monkeypatch.setattr(wireless_module, "get_ipv6_address", lambda i: None)
    module = make_module(Wireless, interface="wlan0")
    monkeypatch.setattr(module, "_get_wireless_info", lambda i: {})
    module.post_config_hook()

    result = module.wireless()

    assert result["full_text"] == "W: down"
    assert result["color"] == "#FF0000"


def test_wireless_first_resolves_interface(make_module, monkeypatch):
    import py3status.i3status.modules.wireless as wireless_module

    Wireless = wireless_module.Py3status

    monkeypatch.setattr(wireless_module, "resolve_first_interface", lambda net_type: "wlan7")
    module = make_module(Wireless, interface="_first_")
    module.post_config_hook()

    assert module.interface == "wlan7"


def test_wireless_first_is_case_insensitive(make_module, monkeypatch):
    # matches real i3status exactly: strcasecmp(title, "_first_") - the
    # special value is recognized regardless of case
    import py3status.i3status.modules.wireless as wireless_module

    Wireless = wireless_module.Py3status

    monkeypatch.setattr(wireless_module, "resolve_first_interface", lambda net_type: "wlan7")
    module = make_module(Wireless, interface="_FIRST_")
    module.post_config_hook()

    assert module.interface == "wlan7"


def test_wireless_handles_no_interface_configured(make_module):
    # interface explicitly set to None (not the "_first_" default) and no
    # wireless interface resolvable at all
    import py3status.i3status.modules.wireless as wireless_module

    Wireless = wireless_module.Py3status

    module = make_module(Wireless, interface=None)
    module.post_config_hook()

    result = module.wireless()

    assert result["full_text"] == "W: down"
    assert result["color"] == "#FF0000"


def test_wireless_default_interface_is_first(make_module, monkeypatch):
    # "_first_" is the class default, so an unconfigured module should
    # auto-resolve to whatever resolve_first_interface() finds
    import py3status.i3status.modules.wireless as wireless_module

    Wireless = wireless_module.Py3status

    monkeypatch.setattr(wireless_module, "resolve_first_interface", lambda net_type: "wlan9")
    module = make_module(Wireless)
    module.post_config_hook()

    assert module.interface == "wlan9"
