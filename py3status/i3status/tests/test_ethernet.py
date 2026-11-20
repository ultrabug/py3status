"""Tests for the ethernet i3status-compatible module."""

import os

import pytest


def test_ethernet_prefers_ipv4(make_module, monkeypatch):
    import py3status.i3status.modules.ethernet as ethernet_module

    Ethernet = ethernet_module.Py3status

    monkeypatch.setattr(ethernet_module, "get_ipv4_address", lambda i: "192.168.1.5")
    monkeypatch.setattr(ethernet_module, "get_ipv6_address", lambda i: "fe80::1")

    module = make_module(Ethernet, interface="eth0")
    monkeypatch.setattr(module, "_is_running", lambda i: True)
    monkeypatch.setattr(module, "_get_speed", lambda i: "1 Gbit/s")
    module.py3.COLOR_GOOD = "#00FF00"
    module.post_config_hook()

    result = module.ethernet()

    assert result["full_text"] == "E: 192.168.1.5 (1 Gbit/s)"
    assert result["color"] == "#00FF00"


def test_ethernet_falls_back_to_ipv6(make_module, monkeypatch):
    import py3status.i3status.modules.ethernet as ethernet_module

    Ethernet = ethernet_module.Py3status

    monkeypatch.setattr(ethernet_module, "get_ipv4_address", lambda i: None)
    monkeypatch.setattr(ethernet_module, "get_ipv6_address", lambda i: "fe80::1")

    module = make_module(Ethernet, interface="eth0")
    monkeypatch.setattr(module, "_is_running", lambda i: True)
    monkeypatch.setattr(module, "_get_speed", lambda i: "?")
    module.py3.COLOR_GOOD = "#00FF00"
    module.post_config_hook()

    result = module.ethernet()

    assert result["full_text"] == "E: fe80::1 (?)"
    assert result["color"] == "#00FF00"


def test_ethernet_no_ip_but_running(make_module, monkeypatch):
    import py3status.i3status.modules.ethernet as ethernet_module

    Ethernet = ethernet_module.Py3status

    monkeypatch.setattr(ethernet_module, "get_ipv4_address", lambda i: None)
    monkeypatch.setattr(ethernet_module, "get_ipv6_address", lambda i: None)

    module = make_module(Ethernet, interface="eth0")
    monkeypatch.setattr(module, "_is_running", lambda i: True)
    monkeypatch.setattr(module, "_get_speed", lambda i: "?")
    module.py3.COLOR_DEGRADED = "#FFFF00"
    module.post_config_hook()

    result = module.ethernet()

    assert result["full_text"] == "E: no IP (?)"
    assert result["color"] == "#FFFF00"


def test_ethernet_down(make_module, monkeypatch):
    import py3status.i3status.modules.ethernet as ethernet_module

    Ethernet = ethernet_module.Py3status

    monkeypatch.setattr(ethernet_module, "get_ipv4_address", lambda i: None)
    monkeypatch.setattr(ethernet_module, "get_ipv6_address", lambda i: None)

    module = make_module(Ethernet, interface="eth0")
    monkeypatch.setattr(module, "_is_running", lambda i: False)
    module.post_config_hook()

    result = module.ethernet()

    assert result["full_text"] == "E: down"
    assert result["color"] == "#FF0000"


def test_ethernet_ipv4_via_real_ioctl_on_loopback():
    # exercises the actual ioctl path (not mocked) against the always-present
    # loopback interface, verified against real i3status's own output
    import py3status.i3status.modules.ethernet as ethernet_module

    get_ipv4_address = ethernet_module.get_ipv4_address
    get_ipv6_address = ethernet_module.get_ipv6_address

    assert get_ipv4_address("lo") == "127.0.0.1"
    assert get_ipv6_address("lo") == "::1"


def test_ethernet_get_speed_reads_real_link_speed():
    # best-effort sanity check against real hardware: exercises the actual
    # ETHTOOL_GSET ioctl path (not mocked) against a link that reports a
    # nonzero speed - skipped rather than failed when this environment has
    # no such interface (eg CI, or a machine with no cable plugged in).
    # Confirmed against the real i3status binary on a live 100 Mbit/s link:
    # both produced the exact same "E: <ip> (100 Mbit/s)" full_text.
    import py3status.i3status.modules.ethernet as ethernet_module

    _get_speed = ethernet_module.Py3status._get_speed

    speed = None
    for ifname in sorted(os.listdir("/sys/class/net")):
        if ifname == "lo":
            continue
        try:
            with open(f"/sys/class/net/{ifname}/carrier") as f:
                has_carrier = f.read().strip() == "1"
        except OSError:
            continue
        if not has_carrier:
            continue
        result = _get_speed(ifname)
        if result != "?":
            speed = result
            break

    if speed is None:
        pytest.skip("no real ethernet link with a nonzero reported speed in this environment")

    assert speed.endswith(("Mbit/s", "Gbit/s"))


def test_ethernet_first_resolves_interface(make_module, monkeypatch):
    import py3status.i3status.modules.ethernet as ethernet_module

    Ethernet = ethernet_module.Py3status

    monkeypatch.setattr(ethernet_module, "resolve_first_interface", lambda net_type: "eth7")
    module = make_module(Ethernet, interface="_first_")
    module.post_config_hook()

    assert module.interface == "eth7"


def test_ethernet_first_is_case_insensitive(make_module, monkeypatch):
    # matches real i3status exactly: strcasecmp(title, "_first_") - the
    # special value is recognized regardless of case
    import py3status.i3status.modules.ethernet as ethernet_module

    Ethernet = ethernet_module.Py3status

    monkeypatch.setattr(ethernet_module, "resolve_first_interface", lambda net_type: "eth7")
    module = make_module(Ethernet, interface="_FIRST_")
    module.post_config_hook()

    assert module.interface == "eth7"


def test_ethernet_helpers_handle_none_interface_gracefully():
    # module_test.py --term style invocation with no interface configured
    # must degrade gracefully, not crash
    import py3status.i3status.modules.ethernet as ethernet_module

    get_ipv4_address = ethernet_module.get_ipv4_address
    get_ipv6_address = ethernet_module.get_ipv6_address
    _get_speed = ethernet_module.Py3status._get_speed
    _is_running = ethernet_module.Py3status._is_running

    assert get_ipv4_address(None) is None
    assert get_ipv6_address(None) is None
    assert _is_running(None) is False
    assert _get_speed(None) == "?"


def test_ethernet_default_interface_is_first(make_module, monkeypatch):
    import py3status.i3status.modules.ethernet as ethernet_module

    Ethernet = ethernet_module.Py3status

    monkeypatch.setattr(ethernet_module, "resolve_first_interface", lambda net_type: "eth9")
    module = make_module(Ethernet)
    module.post_config_hook()

    assert module.interface == "eth9"
