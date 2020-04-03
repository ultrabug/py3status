"""
Display status of a TCP port on a given host.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{host}:{port} {state}')
    host: name of host to check for (default 'localhost')
    icon_off: show this when unavailable (default 'DOWN')
    icon_on: show this when available (default 'UP')
    port: number of port to check for (default 22)

Format placeholders:
    {state} port state

Color options:
    color_down: Closed, default to color_bad
    color_up: Open, default to color_good

@author obb, Moritz Lüdecke

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'localhost:22 UP'}

down
{'color': '#FF0000', 'full_text': u'localhost:22 DOWN'}
"""
import socket


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{host}:{port} {state}"
    host = "localhost"
    icon_off = "DOWN"
    icon_on = "UP"
    port = 22

    def post_config_hook(self):
        self.color_on = self.py3.COLOR_UP or self.py3.COLOR_GOOD
        self.color_off = self.py3.COLOR_DOWN or self.py3.COLOR_BAD

    def check_tcp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.host, self.port))

        if result:
            color = self.color_off
            state = self.icon_off
        else:
            color = self.color_on
            state = self.icon_on

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"state": state}),
            "color": color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
