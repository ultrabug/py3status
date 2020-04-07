"""
Display status of Dropbox daemon.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default "Dropbox: {status}")
    status_busy: text for placeholder {status} when Dropbox is busy
        (default None)
    status_off: text for placeholder {status} when Dropbox isn't running
        (default "isn't running")
    status_on: text for placeholder {status} when Dropbox is up to date
        (default "Up to date")

Value for `status_off` if not set:
    - Dropbox isn't running!

Value for `status_on` if not set:
    - Up to date

Values for `status_busy` if not set:
    - Connecting...
    - Starting...
    - Downloading file list...
    - Syncing "filename"

Format placeholders:
    {status} Dropbox status

Color options:
    color_bad: Not running
    color_degraded: Busy
    color_good: Up to date

Requires:
    dropbox-cli: command line interface for dropbox

Notes:
    Some distributions offer an option to install dropbox-cli. If you don't see
    one for your distribution, then you need to download CLI Python script,
    https://www.dropbox.com/help/desktop-web/linux-commands#commands, rename
    it to `dropbox-cli`, make the script executable and available in your PATH.

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'Dropbox: Up to date'}

busy
{'color': '#FFFF00', 'full_text': 'Dropbox: Syncing "Calorie_Counting.ods"'}

off
{'color': '#FF0000', 'full_text': "Dropbox: isn't running"}
"""

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "Dropbox: {status}"
    status_busy = None
    status_off = "isn't running"
    status_on = "Up to date"

    class Meta:
        deprecated = {
            "format_fix_unnamed_param": [
                {
                    "param": "format",
                    "placeholder": "status",
                    "msg": "{} should not be used in format use `{status}`",
                }
            ]
        }

    def post_config_hook(self):
        if not self.py3.check_commands("dropbox-cli"):
            raise Exception(STRING_NOT_INSTALLED)

    def dropboxd_status(self):
        status = self.py3.command_output(
            "dropbox-cli status", localized=True
        ).splitlines()[0]

        if status == "Dropbox isn't running!":
            color = self.py3.COLOR_BAD
            status = self.status_off
        elif status == "Up to date":
            color = self.py3.COLOR_GOOD
            status = self.status_on
        else:
            color = self.py3.COLOR_DEGRADED
            if self.status_busy is not None:
                status = self.status_busy

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": color,
            "full_text": self.py3.safe_format(self.format, {"status": status}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
