"""
Display number of pending updates for Fedora Linux.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 600)
    format: display format for this module
        (default "DNF [\?if=security&color=bad {available}|\?color=available {available}]")
    thresholds: specify color thresholds to use
        (default [(0, 'good'), (1, 'degraded')])

Format placeholders:
    {available} number of pending available updates
    {bugfix} number of pending bugfix updates
    {enhancement} number of pending enhancement updates
    {security} number of pending security updates
    {unspecified} number of pending unspecified updates

Color thresholds:
    format:
        `xxx`: print a color based on the value of `xxx` placeholder

Examples:
```
# i3status theme
dnf_updates {
    format = "[\?if=security&color=bad DNF: {available}"
    format += "|\?color=available DNF: {available}]"
}

# hide module when no available updates
dnf_updates {
    format = "[\?if=available DNF [\?if=security&color=bad {available}"
    format += "|\?color=available {available}]]"
}

# individual colorized updates
dnf_updates {
    format = "[\?if=security SECURITY [\?color=tomato {security}]][\?soft  ]"
    format += "[\?if=bugfix BUGFIX [\?color=limegreen {bugfix}]][\?soft  ]"
    format += "[\?if=enhancement ENHANCEMENT [\?color=lightskyblue {enhancement}]][\?soft  ]"
    format += "[\?if=unspecified OTHER [\?color=darkgray {unspecified}]]"
}
```

@author tobes
@license BSD

SAMPLE OUTPUT
[{'full_text': 'DNF '}, {'full_text': '14', 'color': '#FF0000'}]

no_updates
[{'full_text': 'DNF '}, {'full_text': '0', 'color': '#00FF00'}]
"""

from collections import Counter
from json import loads

ADVISORIES = ["available", "bugfix", "enhancement", "security", "unspecified"]


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 600
    format = "DNF [\?if=security&color=bad {available}|\?color=available {available}]"
    thresholds = [(0, "good"), (1, "degraded")]

    def post_config_hook(self):
        self.thresholds_init = self.py3.get_color_names_list(self.format, ADVISORIES)

    def _get_dnf_data(self):
        try:
            updates = loads(self.py3.command_output("dnf updateinfo list --json"))
            temporary = (
                dict.fromkeys(ADVISORIES, 0)
                | Counter(x['type'] for x in updates)
                | {ADVISORIES[0]: len(updates)}
            )
            cached_until = self.cache_timeout
        except self.py3.CommandError:
            temporary = dict.fromkeys(ADVISORIES, None)
            cached_until = 10

        return (temporary, cached_until)

    def dnf_updates(self):
        (dnf_data, cached_until) = self._get_dnf_data()

        for x in self.thresholds_init:
            self.py3.threshold_get_color(dnf_data[x], x)

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, dnf_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
