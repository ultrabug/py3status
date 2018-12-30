# -*- coding: utf-8 -*-
"""
Display status of a given hackerspace.

Configuration parameters:
    button_url: mouse button to open URL sent in space's API (default 3)
    cache_timeout: refresh interval for this module (default 60)
    format: display format for this module (default '{state}[ {lastchanged}]')
    format_lastchanged: display format for time (default 'since %H:%M')
    state_closed: show when hackerspace is closed (default 'closed')
    state_open: show when hackerspace is open (default 'open')
    url: specify JSON URL of a hackerspace to retrieve from
        (default 'https://status.chaospott.de/status.json')

Format placeholders:
    {state} Hackerspace state
    {lastchanged} Time

format_lastchanged conversion:
    '%' Strftime characters to be translated

Color options:
    color_closed: Space closed, defaults to color_bad
    color_open: Space open, defaults to color_good

@author timmszigat
@license WTFPL <http://www.wtfpl.net/txt/copying/>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'open since 05:41'}

closed
{'color': '#FF0000', 'full_text': 'closed since 16:38'}
"""

import datetime

STRING_UNAVAILABLE = "spaceapi: N/A"


class Py3status:
    """
    """

    # available configuration parameters
    button_url = 3
    cache_timeout = 60
    format = "{state}[ {lastchanged}]"
    format_lastchanged = "since %H:%M"
    state_closed = "closed"
    state_open = "open"
    url = "https://status.chaospott.de/status.json"

    class Meta:
        deprecated = {
            "rename": [
                {
                    "param": "open_color",
                    "new": "color_open",
                    "msg": "obsolete parameter use `color_open`",
                },
                {
                    "param": "closed_color",
                    "new": "color_closed",
                    "msg": "obsolete parameter use `color_closed`",
                },
                {
                    "param": "closed_text",
                    "new": "state_closed",
                    "msg": "obsolete parameter use `state_closed`",
                },
                {
                    "param": "open_text",
                    "new": "state_open",
                    "msg": "obsolete parameter use `state_open`",
                },
                {
                    "param": "time_text",
                    "new": "format_lastchanged",
                    "msg": "obsolete parameter use `format_lastchanged`",
                },
            ]
        }

    def post_config_hook(self):
        self.button_refresh = 2
        self.color_open = self.py3.COLOR_OPEN or self.py3.COLOR_GOOD
        self.color_closed = self.py3.COLOR_CLOSED or self.py3.COLOR_BAD

    def spaceapi(self):
        color = self.color_closed
        state = self.state_closed
        lastchanged = "unknown"

        try:
            data = self.py3.request(self.url).json()
            self._url = data.get("url")

            if data["state"]["open"]:
                color = self.color_open
                state = self.state_open

            if "lastchange" in data["state"].keys():
                try:
                    dt = datetime.datetime.fromtimestamp(data["state"]["lastchange"])
                    lastchanged = dt.strftime(self.format_lastchanged)
                except TypeError:
                    pass

            full_text = self.py3.safe_format(
                self.format, {"state": state, "lastchanged": lastchanged}
            )

        except (self.py3.RequestException, KeyError):
            full_text = STRING_UNAVAILABLE

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
            "color": color,
        }

    def on_click(self, event):
        button = event["button"]
        if self._url and self.button_url == button:
            self.py3.command_run("xdg-open {}".format(self._url))
            self.py3.prevent_refresh()
        elif button != self.button_refresh:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
