r"""

Display glucose readings from your Dexcom CGM system.

Dexcom CGM systems provide glucose readings up to every five minutes. Designed
to help diabetes patients keep track of their blood glucose levels with ease.

Configuration parameters:
    format: display format for this module
        *(default "Dexcom [\?color=mg_dl {mg_dl} mg/dL {trend_arrow}] [\?color=darkgrey {datetime}]")*
    format_datetime: specify strftime characters to format (default {"datetime": "%-I:%M %p"})
    ous: specify whether if the Dexcom Share user is outside of the US (default False)
    password: specify password for the Dexcom Share user (default None)
    thresholds: specify color thresholds to use
        *(default {
            "mg_dl": [(55, "bad"), (70, "degraded"), (80, "good"), (130, "degraded"), (180, "bad")],
            "mmol_l": [(3.1, "bad"), (3.9, "degraded"), (4.4, "good"), (7.2, "degraded"), (10.0, "bad")],
        })*
    username: specify username for the Dexcom Share user, not follower (default None)

Format placeholders:
    {mg_dl} blood glucose value in mg/dL, eg 80
    {mmol_l} blood glucose value in mmol/L, eg 4.4
    {trend} blood glucose trend information, eg 4
    {trend_direction} blood glucose trend direction, eg Flat
    {trend_description} blood glucose trend information description, eg steady
    {trend_arrow} blood glucose trend as unicode arrow, eg →
    {datetime} glucose reading recorded time as datetime

format_datetime placeholders:
    key: epoch_placeholder, eg {datetime}
    value: % strftime characters to be translated, eg '%b %d' ----> 'Jan 1'

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    pydexcom: A simple Python API to interact with Dexcom Share service

Notes:
    IF GLUCOSE ALERTS AND CGM READINGS DO NOT MATCH SYMPTOMS OR EXPECTATIONS,
    USE A BLOOD GLUCOSE METER TO MAKE DIABETES TREATMENT DECISIONS.

Examples:
```
# compact
dexcom {
    format = "[\?color=mg_dl {mg_dl} {trend_arrow}][\?color=darkgrey {datetime}]"
    format_datetime = {"datetime": "%-I:%M"}
}
```

@author lasers

SAMPLE OUTPUT
[
    {"full_text": "Dexcom "},
    {"full_text": "80 mg/dL →", "color": "#00FF00"},
    {"full_text": "7:15 PM", "color": "#A9A9A9"}
]
"""

from datetime import datetime, timedelta

from pydexcom import Dexcom

STRING_ERROR = "no glucose reading"
CACHE_TIMEOUT = 5 * 60


class Py3status:
    """ """

    # available configuration parameters
    format = r"Dexcom [\?color=mg_dl {mg_dl} mg/dL {trend_arrow}] [\?color=darkgrey {datetime}]"
    format_datetime = {"datetime": "%-I:%M %p"}
    ous = False
    password = None
    thresholds = {
        "mg_dl": [
            (55, "bad"),
            (70, "degraded"),
            (80, "good"),
            (130, "degraded"),
            (180, "bad"),
        ],
        "mmol_l": [
            (3.1, "bad"),
            (3.9, "degraded"),
            (4.4, "good"),
            (7.2, "degraded"),
            (10.0, "bad"),
        ],
    }
    username = None

    def post_config_hook(self):
        for x in ["username", "password"]:
            if not getattr(self, x):
                raise Exception(f"missing `{x}`")

        self.init = {"datetimes": []}
        for x in ["datetime"]:
            if self.py3.format_contains(self.format, x) and x in self.format_datetime:
                self.init["datetimes"].append(x)

        self.seconds = CACHE_TIMEOUT + getattr(self, "cached_delay", 10)
        self.placeholders = ["value", "datetime", "mg_dl", "mmol_l", "trend"]
        self.placeholders += ["trend_arrow", "trend_description", "trend_direction"]
        self.thresholds_init = self.py3.get_color_names_list(self.format)
        self.dexcom_class = Dexcom(self.username, self.password, ous=self.ous)

    def _get_glucose_data(self):
        glucose_reading = self.dexcom_class.get_current_glucose_reading()
        if not glucose_reading:
            self.py3.error(STRING_ERROR, timeout=self.seconds)

        data = {x: getattr(glucose_reading, x) for x in self.placeholders}
        data["datetime"] = data["datetime"].isoformat()
        return data

    def _get_next_datetime(self, data):
        last_datetime = datetime.fromisoformat(data["datetime"])
        next_datetime = last_datetime + timedelta(seconds=self.seconds)
        return (next_datetime - datetime.now()).total_seconds()

    def dexcom(self):
        glucose_data = self._get_glucose_data()
        cached_until = self._get_next_datetime(glucose_data)

        for x in self.init["datetimes"]:
            if x in glucose_data:
                obj = datetime.fromisoformat(glucose_data[x])
                date_format = datetime.strftime(obj, self.format_datetime[x])
                glucose_data[x] = self.py3.safe_format(date_format)

        for x in self.thresholds_init:
            if x in glucose_data:
                self.py3.threshold_get_color(glucose_data[x], x)

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, glucose_data),
        }

    def on_click(self, event):
        self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from os import getenv

    from py3status.module_test import module_test

    config = {"username": getenv("DEXCOM_USERNAME"), "password": getenv("DEXCOM_PASSWORD")}
    module_test(Py3status, config)
