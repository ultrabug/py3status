# -*- coding: utf-8 -*-
"""
This module launch a simple query on each nameservers for the specified domain.
Nameservers are dynamically retrieved. The FQDN is the only one mandatory parameter.
It's also possible to add additional nameservers by appending them in nameservers list.

The default resolver can be overwritten with my_resolver.nameservers parameter.

Written and contributed by @nawadanp
"""

import dns.resolver
import socket


class Py3status:
    """
    Configuration parameters:
        - domain : domain name to check
        - lifetime : resolver lifetime
        - nameservers : comma separated list of reference DNS nameservers
        - resolvers : comma separated list of DNS resolvers to use
    """
    # available configuration parameters
    domain = ''
    lifetime = 0.3
    nameservers = ''
    resolvers = ''

    def ns_checker(self, i3s_output_list, i3s_config):
        response = {'full_text': ''}
        counter = 0
        error = False
        nameservers = []

        # parse some configuration parameters
        if not isinstance(self.nameservers, list):
            self.nameservers = self.nameservers.split(',')
        if not isinstance(self.resolvers, list):
            self.resolvers = self.resolvers.split(',')

        my_resolver = dns.resolver.Resolver()
        my_resolver.lifetime = self.lifetime
        if self.resolvers:
            my_resolver.nameservers = self.resolvers

        my_ns = my_resolver.query(self.domain, 'NS')

        # Insert each NS ip address in nameservers
        for ns in my_ns:
            nameservers.append(str(socket.gethostbyname(str(ns))))
        for ns in self.nameservers:
            nameservers.append(str(ns))

        # Perform a simple DNS query, for each NS servers
        for ns in nameservers:
            my_resolver.nameservers = [ns]
            counter += 1
            try:
                my_resolver.query(self.domain, 'A')
            except:
                error = True

        if error:
            response['full_text'] = str(counter) + ' NS NOK'
            response['color'] = i3s_config['color_bad']
        else:
            response['full_text'] = str(counter) + ' NS OK'
            response['color'] = i3s_config['color_good']

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.ns_checker([], {}))
        sleep(1)
