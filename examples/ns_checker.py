import dns.resolver
import socket


class Py3status:
    """
    This module launch a simple query on each nameservers for the specified domain.
    Nameservers are dynamically retrieved. The FQDN is the only one mandatory parameter.
    It's also possible to add additional nameservers by appending them in nameservers list.

    The default resolver can be overwritten with my_resolver.nameservers parameter.

    Written and contributed by @nawadanp
    """
    def __init__(self):
        self.domain = 'google.com'
        self.lifetime = 0.3
        self.resolver = []
        self.nameservers = []

    def ns_checker(self, i3status_output_json, i3status_config):
        response = {'full_text': '', 'name': 'ns_checker'}
        position = 0
        counter = 0
        error = False
        nameservers = []

        my_resolver = dns.resolver.Resolver()
        my_resolver.lifetime = self.lifetime
        if self.resolver:
            my_resolver.nameservers = self.resolver

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
            response['color'] = i3status_config['color_bad']
        else:
            response['full_text'] = str(counter) + ' NS OK'
            response['color'] = i3status_config['color_good']

        return (position, response)
