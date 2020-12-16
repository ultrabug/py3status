"""
Displays upcoming khal events.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 60)
    config_path: Path to khal configuration file. The default None resolves to /home/$USER/.config/khal/config (default None)
    date_end: Until which datetime the module searches for events (default 'eod')
    format: display format for this module (default '{appointments}')
    output_format: khal conform format for displaying event output (default '{start-time} {title}')

Format placeholders:
    {appointments} list of events in time range

Requires:
    khal: https://github.com/pimutils/khal

@author @xenrox
@license BSD

SAMPLE OUTPUT
{'full_text': '13:00 Eat lunch'}

"""
from datetime import datetime
from re import compile as re_compile
from khal.settings import get_config
from khal.cli import build_collection
from khal.controllers import khal_list


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 60
    config_path = None
    date_end = "eod"
    format = "{appointments}"
    output_format = "{start-time} {title}"

    def _format_output(self, output):
        ansi_escape = re_compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", output)

    def _init_config(self):
        self.config = get_config(self.config_path)
        self.collection = build_collection(self.config, None)
        self.datetimeformat = self.config["locale"]["datetimeformat"]

    def khal_calendar(self):
        self._init_config()
        daterange = (
            str(datetime.now().strftime(self.datetimeformat)) + " " + self.date_end
        )
        output = khal_list(self.collection, daterange, self.config, self.output_format)
        output = [self._format_output(x) for x in output[1:]]

        output = " ".join(output)
        khal_data = {"appointments": output}
        return {
            "full_text": self.py3.safe_format(self.format, khal_data),
            "cached_until": self.py3.time_in(self.cache_timeout),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {"always_show": True}
    from py3status.module_test import module_test

    module_test(Py3status, config=config)
