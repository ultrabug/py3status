"""Tests for the ipv6 i3status-compatible module."""


def test_ipv6_no_connectivity_matches_real_i3status(make_module):
    # confirmed against the real binary in this sandbox (no global IPv6
    # route available): full_text == "no IPv6", color_bad
    import py3status.i3status.modules.ipv6 as ipv6_module

    Ipv6 = ipv6_module.Py3status

    module = make_module(Ipv6)
    module.post_config_hook()

    result = module.ipv6()

    assert result["full_text"] == "no IPv6"
    assert result["color"] == "#FF0000"


def test_ipv6_with_connectivity(make_module, monkeypatch):
    import py3status.i3status.modules.ipv6 as ipv6_module

    Ipv6 = ipv6_module.Py3status

    module = make_module(Ipv6, format_up="%ip")
    monkeypatch.setattr(ipv6_module, "get_outbound_ipv6_address", lambda: "2001:db8::1")
    module.py3.COLOR_GOOD = "#00FF00"
    module.post_config_hook()

    result = module.ipv6()

    assert result["full_text"] == "2001:db8::1"
    assert result["color"] == "#00FF00"


def test_ipv6_iface_only_looked_up_when_used(make_module, monkeypatch):
    import py3status.i3status.modules.ipv6 as ipv6_module

    Ipv6 = ipv6_module.Py3status

    module = make_module(Ipv6, format_up="%ip")
    monkeypatch.setattr(ipv6_module, "get_outbound_ipv6_address", lambda: "2001:db8::1")
    lookups = []
    monkeypatch.setattr(ipv6_module, "get_ipv6_iface", lambda addr: lookups.append(addr) or "eth0")

    module.post_config_hook()
    module.ipv6()
    assert lookups == []

    module.format_up = "%ip on %iface"
    result = module.ipv6()
    assert lookups == ["2001:db8::1"]
    assert result["full_text"] == "2001:db8::1 on eth0"
