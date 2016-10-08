# -*- coding: utf-8 -*-
"""
Display the list of current IPs.

This can exclude specified IPs and displays "no connection" if there are no IPs
to display.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds.
        (default 30)
    ignore: list of IPs to ignore. Can use shell style wildcards.
        (default ['127.*'])
    no_connection: string to display if there are no non-ignored IPs
        (default 'no connection')
    separator: string to use between IPs.
        (default ' ')
"""


# import your useful libs here
import socket
import struct
import fcntl
import array
from fnmatch import fnmatch


class Py3status:
    cache_timeout = 30
    ignore = ['127.*']
    no_connection = 'no connection'
    separator = ' '

    def __init__(self):
        pass

    def ip_list(self):
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': ''
        }

        ip = []
        ifaces = self._list_ifaces()
        for iface in ifaces:
            addr = self._get_ip(iface)
            add = True
            for ignore in self.ignore:
                if fnmatch(addr, ignore):
                    add = False
                    break
            if add:
                ip.append(addr)
        if len(ip) == 0:
            response['full_text'] = self.no_connection
            response['color'] = self.py3.COLOR_BAD
        else:
            response['full_text'] = self.separator.join(ip)
            response['color'] = self.py3.COLOR_GOOD

        return response

    def _list_ifaces(self):
        SIOCGIFCONF = 0x8912
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd = sock.fileno()
        max_possible = 128  # arbitrary. raise if needed.
        data = max_possible * 32
        names = array.array('B', [0]) * data
        outbytes = struct.unpack('iL', fcntl.ioctl(sockfd, SIOCGIFCONF,
                                 struct.pack('iL', data,
                                             names.buffer_info()[0])))[0]
        namestr = names.tostring()
        lst = []
        for i in range(0, outbytes, 40):
            name = namestr[i:i+16].split(b'\x00', 1)[0]
            lst.append(name)
        return lst

    def _get_ip(self, iface):
        SIOCGIFADDR = 0x8915
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd = sock.fileno()
        ifreq = struct.pack('16sH14s', iface, socket.AF_INET, b'\x00'*14)
        try:
            res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
        except:
            return None
        ip = struct.unpack('16sH2x4s8x', res)[2]
        return socket.inet_ntoa(ip)

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
