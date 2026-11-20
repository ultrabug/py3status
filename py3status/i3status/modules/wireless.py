"""
Native reimplementation of i3status's `wireless` module.

Gets the link quality, frequency and ESSID of the given wireless
network interface.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format_bitrate: printf-style format for %bitrate (default '%g %cb/s')
    format_down: format used when there is no association
        (default 'W: down')
    format_noise: printf-style format for %noise (default '%3d%s')
    format_quality: printf-style format for %quality (default '%3d%s')
    format_signal: printf-style format for %signal (default '%3d%s')
    format_up: see placeholders below
        (default 'W: (%quality at %essid, %bitrate) %ip')
    interface: wireless interface to query; the special value
        '_first_' (case-insensitive) picks the first non-virtual,
        non-loopback wireless interface that already has an IPv4 or
        IPv6 address (default '_first_')

Format placeholders:
    %quality signal quality, 0-100, or '?' if unavailable
    %signal signal strength in dBm, or '?' if unavailable
    %noise always '?' (see Notes below)
    %essid the associated network's name
    %frequency the channel frequency, eg '5.2 GHz'
    %ip the interface's IPv4 address, or IPv6 if it has none
    %bitrate the current receive bitrate, eg '866.7 Mb/s'

Color options:
    color_good: quality is at/above 50 (the same fixed "average"
        i3status hardcodes)
    color_degraded: quality is below 50, or there's an IP but no
        quality information
    color_bad: down (no association)

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Real i3status has no 'interface' config key - it comes from the
    section's title instead (eg `wireless wlan0 { }` gives
    interface="wlan0"), with '_first_' special-cased the same way as
    this module's own default. This module exposes 'interface' as an
    ordinary config key instead, so it works with zero config; it's
    stripped automatically if the section resolves to the real
    i3status wrapper, since real i3status crashes on an unrecognized
    option.

    Talks to the kernel's nl80211 generic-netlink interface directly
    (the same interface real i3status uses via libnl) - no subprocess,
    no iw/iwconfig.

    %noise is always '?': nl80211 doesn't expose a noise level on
    Linux, matching real i3status.

    quality_max is always 100 on Linux, so %quality always uses
    format_quality. signal/noise's own *_max are never set on Linux,
    so those use a hardcoded format instead ('%d dBm' or '?') -
    format_signal/format_noise exist for schema parity but are
    unreachable in practice.

@author claude
"""

import socket
import struct

from py3status.i3status.helpers import format_placeholders, resolve_cache_timeout
from py3status.i3status.network import get_ipv4_address, get_ipv6_address, resolve_first_interface

NETLINK_GENERIC = 16
GENL_ID_CTRL = 16
CTRL_CMD_GETFAMILY = 3
CTRL_ATTR_FAMILY_ID = 1
CTRL_ATTR_FAMILY_NAME = 2

NLA_ALIGNTO = 4
NLMSG_ERROR = 2
NLMSG_DONE = 3
NLM_F_REQUEST = 0x1
NLM_F_DUMP = 0x300

NL80211_CMD_GET_SCAN = 32
NL80211_CMD_GET_STATION = 17
NL80211_ATTR_IFINDEX = 3
NL80211_ATTR_MAC = 6
NL80211_ATTR_BSS = 47
NL80211_ATTR_STA_INFO = 21

NL80211_BSS_BSSID = 1
NL80211_BSS_FREQUENCY = 2
NL80211_BSS_INFORMATION_ELEMENTS = 6
NL80211_BSS_SIGNAL_MBM = 7
NL80211_BSS_SIGNAL_UNSPEC = 8
NL80211_BSS_STATUS = 9
NL80211_BSS_STATUS_ASSOCIATED = 1
NL80211_BSS_STATUS_IBSS_JOINED = 2

NL80211_STA_INFO_RX_BITRATE = 14
NL80211_RATE_INFO_BITRATE = 1

WLAN_EID_SSID = 0

NOISE_FLOOR_DBM = -90
SIGNAL_MAX_DBM = -20


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format_bitrate = "%g %cb/s"
    format_down = "W: down"
    format_noise = "%3d%s"
    format_quality = "%3d%s"
    format_signal = "%3d%s"
    format_up = "W: (%quality at %essid, %bitrate) %ip"
    interface = "_first_"

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        if self.interface is not None and self.interface.lower() == "_first_":
            self.interface = resolve_first_interface("wireless")
            self.py3.log(f"wireless: '_first_' resolved to {self.interface!r}", "debug")

    @staticmethod
    def _nla_pack(attr_type, data):
        header = struct.pack("=HH", 4 + len(data), attr_type)
        payload = header + data
        return payload + b"\x00" * ((-len(payload)) % NLA_ALIGNTO)

    @staticmethod
    def _nla_parse(data):
        attrs = {}
        offset = 0
        while offset + 4 <= len(data):
            attr_len, attr_type = struct.unpack_from("=HH", data, offset)
            if attr_len < 4:
                break
            attrs[attr_type & 0x3FFF] = data[offset + 4 : offset + attr_len]
            offset += attr_len + ((-attr_len) % NLA_ALIGNTO)
        return attrs

    @staticmethod
    def _nlmsg_pack(nlmsg_type, flags, seq, payload):
        return struct.pack("=IHHII", 16 + len(payload), nlmsg_type, flags, seq, 0) + payload

    def _genl_request(self, sock, family_id, cmd, seq, attrs_payload):
        genlhdr = struct.pack("=BBH", cmd, 1, 0)
        sock.send(
            self._nlmsg_pack(family_id, NLM_F_REQUEST | NLM_F_DUMP, seq, genlhdr + attrs_payload)
        )

    @staticmethod
    def _recv_dump(sock):
        """Yield each genl message payload (past the genlmsghdr) in a dump response."""
        while True:
            buf = sock.recv(65536)
            offset = 0
            while offset < len(buf):
                msg_len, msg_type = struct.unpack_from("=IH", buf, offset)
                if msg_type in (NLMSG_DONE, NLMSG_ERROR):
                    return
                yield buf[offset + 16 : offset + msg_len]
                offset += msg_len + ((-msg_len) % 4)

    def _resolve_nl80211_family(self, sock):
        genlhdr = struct.pack("=BBH", CTRL_CMD_GETFAMILY, 1, 0)
        attr = self._nla_pack(CTRL_ATTR_FAMILY_NAME, b"nl80211\x00")
        sock.send(self._nlmsg_pack(GENL_ID_CTRL, NLM_F_REQUEST, 1, genlhdr + attr))
        buf = sock.recv(65536)
        msg_len = struct.unpack_from("=I", buf, 0)[0]
        attrs = self._nla_parse(buf[20:msg_len])
        if CTRL_ATTR_FAMILY_ID not in attrs:
            return None
        return struct.unpack_from("=H", attrs[CTRL_ATTR_FAMILY_ID])[0]

    @staticmethod
    def _find_ssid(ies):
        offset = 0
        while offset + 2 <= len(ies):
            eid = ies[offset]
            elen = ies[offset + 1]
            if eid == WLAN_EID_SSID:
                return ies[offset + 2 : offset + 2 + elen]
            offset += 2 + elen
        return None

    @staticmethod
    def _xbm_to_percent(xbm, divisor):
        xbm //= divisor
        xbm = max(NOISE_FLOOR_DBM, min(SIGNAL_MAX_DBM, xbm))
        return round(100 - 70 * (SIGNAL_MAX_DBM - xbm) / (SIGNAL_MAX_DBM - NOISE_FLOOR_DBM))

    @staticmethod
    def _print_bitrate(bitrate, format_bitrate):
        rate = float(bitrate)
        if rate >= 1e9:
            scale, divisor = "G", 1e9
        elif rate >= 1e6:
            scale, divisor = "M", 1e6
        else:
            scale, divisor = "k", 1e3
        value = format_bitrate.replace("%g", "%s" % ("%g" % (rate / divisor)))
        return value.replace("%c", scale, 1)

    def _get_wireless_info(self, interface):
        """Return a dict of whatever fields could be determined, or {} if none."""
        info = {}
        try:
            sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, NETLINK_GENERIC)
            sock.bind((0, 0))
        except OSError:
            return info

        try:
            family_id = self._resolve_nl80211_family(sock)
            if family_id is None:
                return info

            ifindex = socket.if_nametoindex(interface)

            payload = self._nla_pack(NL80211_ATTR_IFINDEX, struct.pack("=I", ifindex))
            self._genl_request(sock, family_id, NL80211_CMD_GET_SCAN, 2, payload)

            # Fully drain every message in this dump (don't break early) even
            # after finding the associated BSS - GET_SCAN returns one message
            # per nearby network, and leaving any unread on the socket would
            # corrupt the next request's response (its leftover messages would
            # be read back as if they belonged to that later dump).
            bssid = None
            for msg in self._recv_dump(sock):
                attrs = self._nla_parse(msg[4:])
                if NL80211_ATTR_BSS not in attrs:
                    continue
                bss = self._nla_parse(attrs[NL80211_ATTR_BSS])
                if NL80211_BSS_STATUS not in bss:
                    continue
                status = struct.unpack_from("=I", bss[NL80211_BSS_STATUS])[0]
                if status not in (NL80211_BSS_STATUS_ASSOCIATED, NL80211_BSS_STATUS_IBSS_JOINED):
                    continue

                bssid = bss.get(NL80211_BSS_BSSID)
                if NL80211_BSS_FREQUENCY in bss:
                    info["frequency"] = (
                        struct.unpack_from("=I", bss[NL80211_BSS_FREQUENCY])[0] * 1e6
                    )
                if NL80211_BSS_SIGNAL_UNSPEC in bss:
                    info["signal"] = bss[NL80211_BSS_SIGNAL_UNSPEC][0]
                    info["quality"] = info["signal"]
                if NL80211_BSS_SIGNAL_MBM in bss:
                    mbm = struct.unpack_from("=i", bss[NL80211_BSS_SIGNAL_MBM])[0]
                    info["signal"] = mbm // 100
                    info["quality"] = self._xbm_to_percent(mbm, 100)
                if NL80211_BSS_INFORMATION_ELEMENTS in bss:
                    ssid = self._find_ssid(bss[NL80211_BSS_INFORMATION_ELEMENTS])
                    if ssid:
                        info["essid"] = ssid.decode(errors="replace")

            if bssid is None:
                return info

            payload = self._nla_pack(
                NL80211_ATTR_IFINDEX, struct.pack("=I", ifindex)
            ) + self._nla_pack(NL80211_ATTR_MAC, bssid)
            self._genl_request(sock, family_id, NL80211_CMD_GET_STATION, 3, payload)

            for msg in self._recv_dump(sock):
                attrs = self._nla_parse(msg[4:])
                if NL80211_ATTR_STA_INFO not in attrs:
                    continue
                sinfo = self._nla_parse(attrs[NL80211_ATTR_STA_INFO])
                if NL80211_STA_INFO_RX_BITRATE not in sinfo:
                    continue
                rinfo = self._nla_parse(sinfo[NL80211_STA_INFO_RX_BITRATE])
                if NL80211_RATE_INFO_BITRATE in rinfo:
                    bitrate_100kbit = struct.unpack_from("=H", rinfo[NL80211_RATE_INFO_BITRATE])[0]
                    info["bitrate"] = bitrate_100kbit * 100 * 1000
                break
        except OSError:
            # netlink socket/request failed mid-exchange - return whatever
            # fields were already collected instead of losing them
            pass
        finally:
            sock.close()

        return info

    def wireless(self):
        ipv4 = get_ipv4_address(self.interface)
        ipv6 = get_ipv6_address(self.interface)

        if ipv4 is None and ipv6 is None:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": self.format_down,
                "color": self.py3.COLOR_BAD,
            }
        ip_address = ipv4 if ipv4 is not None else ipv6

        info = self._get_wireless_info(self.interface) if self.interface else {}

        if not info:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": self.format_down,
                "color": self.py3.COLOR_BAD,
            }

        if "quality" in info:
            color = self.py3.COLOR_GOOD if info["quality"] >= 50 else self.py3.COLOR_DEGRADED
        else:
            color = self.py3.COLOR_DEGRADED if ip_address == "no IP" else self.py3.COLOR_GOOD

        quality_str = self.format_quality % (info["quality"], "%") if "quality" in info else "?"
        signal_str = f"{info['signal']} dBm" if "signal" in info else "?"
        noise_str = "?"
        essid_str = info.get("essid", "?")
        frequency_str = f"{info['frequency'] / 1e9:1.1f} GHz" if "frequency" in info else "?"
        bitrate_str = (
            self._print_bitrate(info["bitrate"], self.format_bitrate) if "bitrate" in info else ""
        )

        placeholders = [
            ("%quality", quality_str),
            ("%signal", signal_str),
            ("%noise", noise_str),
            ("%essid", essid_str),
            ("%frequency", frequency_str),
            ("%ip", ip_address),
            ("%bitrate", bitrate_str),
        ]

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(self.format_up, placeholders),
            "color": color,
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
