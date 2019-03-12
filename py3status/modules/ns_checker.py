# -*- coding: utf-8 -*-
"""
Display DNS resolution success on a configured domain.

This module launch a simple query on each nameservers for the specified domain.
Nameservers are dynamically retrieved. The FQDN is the only one mandatory
parameter.  It's also possible to add additional nameservers by appending them
in nameservers list.

The default resolver can be overwritten with my_resolver.nameservers parameter.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 300)
    domain: domain name to check (default '')
    format: output format string (default '{total_count} NS {status}')
    lifetime: resolver lifetime (default 0.3)
    nameservers: comma separated list of reference DNS nameservers (default '')
    resolvers: comma separated list of DNS resolvers to use (default '')

Format placeholders:
    {nok_count} The number of failed name servers
    {ok_count} The number of working name servers
    {status} The overall status of the name servers (OK or NOK)
    {total_count} The total number of name servers

Color options:
    color_bad: One or more lookups have failed
    color_good: All lookups have succeeded

Requires:
    dnspython: a dns toolkit for python

@author nawadanp

SAMPLE OUTPUT
{'full_text': '10 NS OK'}
"""

import dns.resolver
import socket


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 300
    domain = ""
    format = "{total_count} NS {status}"
    lifetime = 0.3
    nameservers = ""
    resolvers = ""

    def ns_checker(self):
        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": self.py3.COLOR_GOOD,
            "full_text": "",
        }
        count_nok = 0
        count_ok = 0
        nameservers = []
        status = "OK"

        # parse some configuration parameters
        if not isinstance(self.nameservers, list):
            self.nameservers = self.nameservers.split(",")
        if not isinstance(self.resolvers, list):
            self.resolvers = self.resolvers.split(",")

        my_resolver = dns.resolver.Resolver()
        my_resolver.lifetime = self.lifetime
        if self.resolvers:
            my_resolver.nameservers = self.resolvers

        my_ns = my_resolver.query(self.domain, "NS")

        # Insert each NS ip address in nameservers
        for ns in my_ns:
            nameservers.append(str(socket.gethostbyname(str(ns))))
        for ns in self.nameservers:
            nameservers.append(str(ns))

        # Perform a simple DNS query, for each NS servers
        for ns in nameservers:
            my_resolver.nameservers = [ns]
            try:
                my_resolver.query(self.domain, "A")
                count_ok += 1
            except:  # noqa e722
                count_nok += 1
                status = "NOK"
                response["color"] = self.py3.COLOR_BAD

        response["full_text"] = self.py3.safe_format(
            self.format,
            dict(
                total_count=len(nameservers),
                nok_count=count_nok,
                ok_count=count_ok,
                status=status,
            ),
        )

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
