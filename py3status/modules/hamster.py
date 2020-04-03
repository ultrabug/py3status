"""
Display time tracking activities from Hamster.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    format: see placeholders below (default '{current}')

Format placeholders:
    {current} current activity

Requires:
    hamster: time tracking application

@author Aaron Fields (spirotot [at] gmail.com)
@license BSD

SAMPLE OUTPUT
{'full_text': 'Watering flowers@Day-to-day (00:03)'}

inactive
{'full_text': 'No activity'}
"""

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{current}"

    def post_config_hook(self):
        if not self.py3.check_commands("hamster"):
            raise Exception(STRING_NOT_INSTALLED)

    def hamster(self):
        activity = self.py3.command_output("hamster current").strip()
        if activity != "No activity":
            activity = activity.split()
            time_elapsed = activity[-1]
            activity = activity[2:-1]
            activity = "{} ({})".format(" ".join(activity), time_elapsed)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"current": activity}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
