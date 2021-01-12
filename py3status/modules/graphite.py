"""
Display Graphite metrics.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds.
        (default 120)
    datapoint_selection: when multiple data points are returned,
        use "max" or "min" to determine which one to display.
        (default "max")
    format: you MUST use placeholders here to display data, see below.
        (default '')
    graphite_url: URL to your graphite server. (default '')
    http_timeout: HTTP query timeout to graphite.
        (default 10)
    proxy: You can configure the proxy with HTTP or HTTPS.
        examples:
            proxy = 'https://myproxy.example.com:1234/'
            proxy = 'http://user:passwd@myproxy.example.com/'
            proxy = 'socks5://user:passwd@host:port'
        (proxy_socks is available after an 'pip install requests[socks]')
        (default None)
    targets: semicolon separated list of targets to query graphite for.
        (default '')
    threshold_bad: numerical threshold,
        if set will send a notification and colorize the output.
        (default None)
    threshold_degraded: numerical threshold,
        if set will send a notification and colorize the output.
        (default None)
    timespan: time range to query graphite for.
        (default "-2minutes")
    value_comparator: choose between "max" and "min" to compare thresholds
        to the data point value.
        (default "max")
    value_format: pretty format long numbers with "K", "M" etc.
        (default True)
    value_round: round values so they're not displayed as floats.
        (default True)

Dynamic format placeholders:
        The "format" parameter placeholders are dynamically based on the data
        points names returned by the "targets" query to graphite.

    For example if your target is `"carbon.agents.localhost-a.memUsage"`,
    you'd get a JSON result like this:

        ```
        {
            "target": "carbon.agents.localhost-a.memUsage",
            "datapoints": [[19693568.0, 1463663040]]
        }
        ```

    So the placeholder you could use on your "format" config is:
        `format = "{carbon.agents.localhost-a.memUsage}"`

    TIP: use aliases !
        ```
        targets = "alias(carbon.agents.localhost-a.memUsage, 'local_memuse')"
        format = "local carbon mem usage: {local_memuse} bytes"
        ```

Color options:
    color_bad: threshold_bad has been exceeded
    color_degraded: threshold_degraded has been exceeded

@author ultrabug

SAMPLE OUTPUT
{'full_text': '412 req/s'}
"""
from requests import get
from syslog import syslog, LOG_INFO


def format_value(num, value_round=True):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1000:
            if value_round:
                return f"{num:1.0f}{unit}"
            else:
                return f"{num:3.1f}{unit}"
        num /= 1000
    if value_round:
        return "{:.0f}{}".format(num, "Y")
    else:
        return "{:.1f}{}".format(num, "Y")


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 120
    datapoint_selection = "max"
    format = ""
    graphite_url = ""
    http_timeout = 10
    proxy = None
    targets = ""
    threshold_bad = None
    threshold_degraded = None
    timespan = "-2minutes"
    value_comparator = "max"
    value_format = True
    value_round = True

    def post_config_hook(self):
        self._validate_config()

    def _validate_config(self):
        if not self.format:
            raise ValueError('missing "format" configuration')
        if not self.graphite_url:
            raise ValueError('missing "graphite_url" configuration')
        if not self.targets:
            raise ValueError('missing "targets" configuration')
        if self.datapoint_selection not in ["max", "min"]:
            raise ValueError('invalid "datapoint_selection" configuration')
        if self.value_comparator not in ["max", "min"]:
            raise ValueError('invalid "value_comparator" configuration')

    def _render_graphite_json(self):
        params = [("format", "json"), ("from", self.timespan)]
        for target in self.targets.split(";"):
            params.append(("target", target))

        proxies = {}
        if self.proxy:
            if self.proxy.startswith("https"):
                proxies["https"] = self.proxy
            else:
                proxies["http"] = self.proxy

        r = get(
            f"{self.graphite_url}/render",
            params,
            timeout=self.http_timeout,
            proxies=proxies,
        )
        if r.status_code != 200:
            raise Exception(f"HTTP error {r.status_code}")
        else:
            color_key = "good"
            r_json = {}
            for metric in r.json():
                value = None
                target = metric["target"]
                for datapoint_list in metric["datapoints"]:
                    point, timestamp = datapoint_list
                    if point is not None:
                        if value is None:
                            value = point
                        elif self.datapoint_selection == "max":
                            value = max(value, point)
                        elif self.datapoint_selection == "min":
                            value = min(value, point)

                if value is None:
                    syslog(
                        LOG_INFO,
                        "graphite module: no data for target {} with configuration {}".format(
                            target, self.targets
                        ),
                    )
                    continue

                if self.value_format:
                    displayed_value = format_value(value, self.value_round)
                else:
                    displayed_value = value

                # compare this value to the configured thresholds
                # and use the worst color to display
                _color = self._check_threshold_and_get_color(
                    displayed_value, target, value
                )
                if _color == "bad":
                    color_key = "bad"
                elif _color == "degraded" and color_key != "bad":
                    color_key = "degraded"

                r_json[target] = displayed_value
            return color_key, r_json

    def _reset_notifications(self):
        self.notification_level = "info"
        self.notifications = []

    def _store_notification(self, target, threshold, value):
        if self.value_comparator == "max":
            msg = f"{target}: {value} > {threshold}"
        elif self.value_comparator == "min":
            msg = f"{target}: {value} < {threshold}"
        self.notifications.append(msg)

    def _notify_user(self):
        if self.notifications:
            self.py3.notify_user(
                "\n".join(self.notifications), level=self.notification_level
            )

    def _check_threshold_and_get_color(self, displayed_value, target, value):
        func = {"max": max, "min": min}
        if self.threshold_bad:
            test = func[self.value_comparator](self.threshold_bad, value)
            if test == value:
                self._store_notification(target, self.threshold_bad, displayed_value)
                self.notification_level = "error"
                return "bad"
        if self.threshold_degraded:
            test = func[self.value_comparator](self.threshold_degraded, value)
            if test == value:
                self._store_notification(
                    target, self.threshold_degraded, displayed_value
                )
                return "degraded"
        return "good"

    def graphite(self):
        self._reset_notifications()

        color_key, r_json = self._render_graphite_json()
        self._notify_user()

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": getattr(self.py3, f"COLOR_{color_key.upper()}"),
            "full_text": self.py3.safe_format(self.format, r_json),
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
