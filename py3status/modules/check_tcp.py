# -*- coding: utf-8 -*-
"""
Display status of a TCP port on a given host.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module
        (default '{host}:{port} [\?if=is_open UP|DOWN]')
    host: specify host name to use (default 'localhost')
    port: specify port number to use (default 22)

Control placeholders:
    is_open: a boolean based on TCP port status
    is_closed: a boolean based on TCP port status

Format placeholders:
    {host} TCP host name
    {port} TCP port number

Color options:
    color_down: Port closed, defaults to color_bad
    color_up: Port open, defaults to color_good

@author obb, Moritz Lüdecke

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'localhost:22 UP'}

down
{'color': '#FF0000', 'full_text': u'localhost:22 DOWN'}
"""

import socket

DEFAULT_FORMAT = '{host}:{port} [\?if=is_open UP|DOWN]'
TRUE = ' '
FALSE = ''


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = DEFAULT_FORMAT
    host = 'localhost'
    port = 22

    def post_config_hook(self):
        self.color_off = self.py3.COLOR_DOWN or self.py3.COLOR_BAD
        self.color_on = self.py3.COLOR_UP or self.py3.COLOR_GOOD

        # DEPRECATION WARNING
        if self.format != DEFAULT_FORMAT:
            return

        icon_off = getattr(self, 'icon_off', None)
        icon_on = getattr(self, 'icon_on', None)

        if self.py3.format_contains(self.format, 'state'):
            new = u'[\?if=is_open {}|{}]'.format(
                icon_on or 'UP',
                icon_off or 'DOWN',
            )
            self.format = self.format.replace('{state}', new)
        else:
            self.format = u'{{host}}:{{port}} [\?if=is_open {}|{}]'.format(
                icon_on or 'UP',
                icon_off or 'DOWN',
            )
        msg = 'DEPRECATION WARNING: you are using old style configuration '
        msg += 'parameters you should update to use the new format.'
        self.py3.log(msg)

    def check_tcp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.host, self.port))

        is_closed = is_open = None

        if result:
            color = self.color_off
            is_closed = True
        else:
            color = self.color_on
            is_open = True

        # TEMPORARY SOLUTION
        is_open = TRUE if is_open else FALSE
        is_closed = TRUE if is_closed else FALSE

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color,
            'full_text': self.py3.safe_format(self.format,
                                              dict(
                                                  is_open=is_open,
                                                  is_closed=is_closed,
                                              ))
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
