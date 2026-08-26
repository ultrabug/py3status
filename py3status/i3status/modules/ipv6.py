"""
Native reimplementation of i3status's `ipv6` module.

This module gets the IPv6 address used for outgoing connections (that
is, the best available public IPv6 address on your computer) and the
interface it is assigned to.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format_down: format used when there is no IPv6 connectivity
        (default 'no IPv6')
    format_up: see placeholders below (default '%ip')

Format placeholders:
    %ip the globally routable IPv6 address
    %iface the interface that address belongs to (only looked up if
        this placeholder is actually used in format_up)

Color options:
    color_good: has connectivity
    color_bad: no connectivity

Type: Singleton (supports only one, unnamed section)

@author claude
"""

from py3status.i3status.helpers import format_placeholders, resolve_cache_timeout
from py3status.i3status.network import get_ipv6_iface, get_outbound_ipv6_address


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format_down = "no IPv6"
    format_up = "%ip"

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)

    def ipv6(self):
        address = get_outbound_ipv6_address()

        if address is None:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": self.format_down,
                "color": self.py3.COLOR_BAD,
            }

        iface = (get_ipv6_iface(address) or "(error)") if "%iface" in self.format_up else ""
        placeholders = [("%ip", address), ("%iface", iface)]

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(self.format_up, placeholders),
            "color": self.py3.COLOR_GOOD,
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
