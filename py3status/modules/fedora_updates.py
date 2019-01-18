"""
Display number of pending updates for Fedora Linux.

This will display a count of how many `dnf` updates are waiting
to be installed. Additionally check for update security notices.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 600)
    check_security: Check for security updates
        (default True)
    format: Display format to use
        (default 'DNF: {updates}')

Format placeholders:
    {updates} number of pending dnf updates

Color options:
    color_bad: Security notice
    color_degraded: Upgrade available
    color_good: No upgrades needed

@author tobes
@license BSD

SAMPLE OUTPUT
{'color': '#FFFF00', 'full_text': 'DNF: 14'}
"""

import subprocess
import re


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 600
    check_security = True
    format = "DNF: {updates}"

    def post_config_hook(self):
        self._reg_ex_sec = re.compile(r"\d+(?=\s+Security)")
        self._reg_ex_pkg = re.compile(b"^\\S+\\.", re.M)
        self._first = True
        self._updates = 0
        self._security_notice = False

    def fedora_updates(self):
        if self._first:
            self._first = False
            response = {
                "cached_until": self.py3.time_in(0),
                "full_text": self.py3.safe_format(self.format, {"updates": "?"}),
            }
            return response

        output, error = subprocess.Popen(
            ["dnf", "check-update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()

        updates = len(self._reg_ex_pkg.findall(output))

        if updates == 0:
            color = self.py3.COLOR_GOOD
            self._updates = 0
            self._security_notice = False
        else:
            if self._updates > updates:
                # we have installed some updates so re-check security
                self._security_notice = False
            if (
                self.check_security
                and not self._security_notice
                and self._updates != updates
            ):
                output, error = subprocess.Popen(
                    ["dnf", "updateinfo"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ).communicate()
                notices = str(output)
                self._security_notice = len(self._reg_ex_sec.findall(notices))
                self._updates = updates
            if self.check_security and self._security_notice:
                color = self.py3.COLOR_BAD
            else:
                color = self.py3.COLOR_DEGRADED

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": color,
            "full_text": self.py3.safe_format(self.format, {"updates": updates}),
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
