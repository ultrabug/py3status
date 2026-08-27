"""Tests for shared network-interface helpers (py3status/i3status/network.py)."""

import py3status.i3status.network as network_module


def test_get_ipv6_address_and_iface_are_inverses_on_loopback():
    # exercises the real /proc/net/if_inet6 parsing (not mocked) against the
    # always-present loopback interface/address
    assert network_module.get_ipv6_address("lo") == "::1"
    assert network_module.get_ipv6_iface("::1") == "lo"


def test_get_ipv6_iface_returns_none_for_unknown_address():
    assert network_module.get_ipv6_iface("2001:db8::dead:beef") is None


def test_get_outbound_ipv6_address_returns_string_or_none():
    # exercises the real UDP-connect probe (not mocked) - this environment
    # may or may not have real IPv6 connectivity, so both outcomes are
    # valid; what matters is it doesn't raise and returns the right shape
    result = network_module.get_outbound_ipv6_address()
    assert result is None or isinstance(result, str)


def test_resolve_first_interface_picks_wireless_with_address(monkeypatch):
    monkeypatch.setattr(network_module.os, "listdir", lambda path: ["lo", "eth0", "wlan0"])
    # lo is excluded by name, the other two are real (non-virtual) devices
    monkeypatch.setattr(network_module, "_iface_is_virtual", lambda ifname: False)
    monkeypatch.setattr(
        network_module,
        "_iface_net_type",
        lambda ifname: "wireless" if ifname == "wlan0" else "ethernet",
    )
    monkeypatch.setattr(
        network_module,
        "get_ipv4_address",
        lambda ifname: "192.168.1.5" if ifname == "wlan0" else None,
    )
    monkeypatch.setattr(network_module, "get_ipv6_address", lambda ifname: None)

    assert network_module.resolve_first_interface("wireless") == "wlan0"
    # eth0 has no address in this fixture, so no ethernet interface qualifies
    assert network_module.resolve_first_interface("ethernet") is None
