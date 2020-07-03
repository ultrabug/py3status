"""
Display response times of the configured Pingdom checks.

We also verify the status of the checks and colorize if needed.
Pingdom API doc : https://www.pingdom.com/features/api/documentation/

Configuration parameters:
    app_key: create an APP KEY on pingdom first (default '')
    cache_timeout: how often to refresh the check from pingdom (default 600)
    checks: comma separated pindgom check names to display (default '')
    format: display format for this module (default '{pingdom}')
    login: pingdom login (default '')
    max_latency: maximal latency before coloring the output (default 500)
    password: pingdom password (default '')
    request_timeout: pindgom API request timeout (default 10)

Format placeholders:
    {pingdom} pingdom response times

Color options:
    color_bad: Site is down
    color_degraded: Latency exceeded max_latency

Requires:
    requests: https://pypi.python.org/pypi/requests

@author ultrabug

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'Pingdom: 323ms'}

degraded
{'color': '#FFFF00', 'full_text': 'Pingdom: 945ms'}

down
{'color': '#FF0000', 'full_text': 'Pingdom: DOWN'}
"""

import requests


class Py3status:
    """
    """

    # available configuration parameters
    app_key = ""
    cache_timeout = 600
    checks = ""
    format = "{pingdom}"
    login = ""
    max_latency = 500
    password = ""
    request_timeout = 10

    def pingdom(self):
        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": "",
        }
        pingdom = None

        # parse some configuration parameters
        if not isinstance(self.checks, list):
            self.checks = self.checks.split(",")

        r = requests.get(
            "https://api.pingdom.com/api/2.0/checks",
            auth=(self.login, self.password),
            headers={"App-Key": self.app_key},
            timeout=self.request_timeout,
        )
        result = r.json()
        if "checks" in result:
            for check in [ck for ck in result["checks"] if ck["name"] in self.checks]:
                if check["status"] == "up":
                    pingdom += "{}: {}ms, ".format(
                        check["name"], check["lastresponsetime"]
                    )
                    if check["lastresponsetime"] > self.max_latency:
                        response["color"] = self.py3.COLOR_DEGRADED
                else:
                    response["color"] = self.py3.COLOR_BAD
                    pingdom += "{}: DOWN".format(check["name"])
            pingdom = pingdom.strip(", ")
            response["full_text"] = self.py3.safe_format(
                self.format, {"pingdom": pingdom}
            )

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
