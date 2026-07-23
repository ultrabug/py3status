r"""
Display glucose readings from LibreLinkUp-connected patients.

LibreLinkUp provides glucose readings every five minutes, allowing
family, friends, and caregivers of LibreLinkUp-connected patients
to easily keep track of their blood glucose levels with ease.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 300)
    format: display format for this module (default '{format_patient}')
    format_datetime: specify strftime characters to format (default {"timestamp": "%-I:%M %p"})
    format_patient: display format for LibreLinkUp-connected patients
        *(default '{first_name} [\?color=mg_dl {mg_dl} mg/dL {trend_arrow}]'
        ' [\?color=darkgrey {timestamp}]')*
    format_patient_separator: show separator if more than one (default ' ')
    password: specify password for the LibreLinkUp account (default None)
    thresholds: specify color thresholds to use
        *(default {
            "mg_dl": [(79, "bad"), (80, "good"), (181, "degraded"), (251, "orange")],
            "mmol_l": [(4.4, "bad"), (4.5, "good"), (10.1, "degraded"), (14.0, "orange")],
        })*
    username: specify username for the LibreLinkUp account (default None)

Format placeholders:
    {format_patient} format for LibreLinkUp-connected patients

format_patient placeholders:
    {factory_timestamp} glucose reading recorded time as datetime (utc aware)
    {first_name} patient first name
    {id} patient id
    {last_name} patient last name
    {mg_dl} blood glucose value in mg/dL, eg 80
    {mmol_l} blood glucose value in mmol/L, eg 4.4
    {patient_id} patient id
    {timestamp} glucose reading recorded time as datetime
    {trend} blood glucose trend information, eg 3
    {trend_arrow} blood glucose trend as unicode arrow, eg →
    {trend_description} blood glucose trend information description, eg Stable

format_datetime placeholders:
    key: epoch_placeholder, eg {timestamp}
    value: % strftime characters to be translated, eg '%b %d' ----> 'Jan 1'

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    pylibrelinkup: A simple Python API to interact with LibreLinkUp service

Notes:
    IF GLUCOSE ALERTS AND CGM READINGS DO NOT MATCH SYMPTOMS OR EXPECTATIONS,
    USE A BLOOD GLUCOSE METER TO MAKE DIABETES TREATMENT DECISIONS.

Examples:
```
# compact version
librelinkup {
    format_patient = "[\?color=mg_dl {mg_dl}{trend_arrow} ][\?color=darkgrey {timestamp}]"
    format_datetime = {"timestamp": "%-I:%M"}
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'Tom Hanks '},
    {'full_text': '80 mg/dL → ', 'color': '#00FF00'},
    {'full_text': '7:15 PM', 'color': '#A9A9A9'},
]
"""

from datetime import datetime

from pylibrelinkup import PyLibreLinkUp

MMOL_L_PER_MG_DL = 18.0182
TREND_ARROW_MAP = {
    "DOWN_FAST": "⇊",
    "DOWN_SLOW": "↓",
    "STABLE": "→",
    "UP_SLOW": "↑",
    "UP_FAST": "⇈",
}


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 300
    format = "{format_patient}"
    format_datetime = {"timestamp": "%-I:%M %p"}
    format_patient = (
        r"{first_name} [\?color=mg_dl {mg_dl} mg/dL {trend_arrow}]"
        r" [\?color=darkgrey {timestamp}]"
    )
    format_patient_separator = " "
    password = None
    thresholds = {
        "mg_dl": [
            (79, "bad"),
            (80, "good"),
            (181, "degraded"),
            (251, "orange"),
        ],
        "mmol_l": [
            (4.4, "bad"),
            (4.5, "good"),
            (10.1, "degraded"),
            (14.0, "orange"),
        ],
    }
    username = None

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {
                        "mg_dl": ":d",
                        "mmol_l": ":.2f",
                    },
                    "format_strings": ["format_patient"],
                }
            ]
        }

    def post_config_hook(self):
        for x in ["username", "password"]:
            if not getattr(self, x):
                raise Exception(f"missing `{x}`")

        self.init = {"datetimes": []}
        for x in ["timestamp", "factory_timestamp"]:
            if self.py3.format_contains(self.format_patient, x) and x in self.format_datetime:
                self.init["datetimes"].append(x)

        self.librelinkup_class = PyLibreLinkUp(email=self.username, password=self.password)
        self.librelinkup_class.authenticate()

    def _consoldiate(self, patient):
        # data
        model_data = patient.model_dump()
        latest_model_data = self.librelinkup_class.latest(patient).model_dump()
        data = model_data | latest_model_data

        # ids
        for key in ("id", "patient_id"):
            data[key] = str(data[key])

        # units
        if "value_in_mg_per_dl" in data:
            v = data["value_in_mg_per_dl"]
            data["mg_dl"] = v
            data["mmol_l"] = v / MMOL_L_PER_MG_DL
        elif "value_in_mmol_per_l" in data:
            v = data["value_in_mmol_per_l"]
            data["mmol_l"] = v
            data["mg_dl"] = v * MMOL_L_PER_MG_DL

        # trends
        trend_name = getattr(data["trend"], "name", str(data["trend"]))
        data["trend_arrow"] = TREND_ARROW_MAP.get(trend_name)
        data["trend_description"] = trend_name.replace("_", " ").title()

        return data

    def librelinkup(self):
        patients = self.librelinkup_class.get_patients()
        new_patient = []

        for patient in patients:
            patient_data = self._consoldiate(patient)

            for x in self.init["datetimes"]:
                obj = datetime.fromisoformat(str(patient_data[x]))
                date_format = obj.strftime(self.format_datetime[x])
                patient_data[x] = self.py3.safe_format(date_format)

            self.py3.threshold_update(patient_data, self.format_patient)

            new_patient.append(self.py3.safe_format(self.format_patient, patient_data))

        format_patient_separator = self.py3.safe_format(self.format_patient_separator)
        format_patient = self.py3.composite_join(format_patient_separator, new_patient)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"format_patient": format_patient}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from os import getenv

    from py3status.module_test import module_test

    config = {
        "username": getenv("LIBRELINKUP_USERNAME"),
        "password": getenv("LIBRELINKUP_PASSWORD"),
    }
    module_test(Py3status, config)
