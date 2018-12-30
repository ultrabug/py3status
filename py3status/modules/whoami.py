# -*- coding: utf-8 -*-
"""
Display logged-in username.

Configuration parameters:
    format: display format for this module (default '{username}')

Format placeholders:
    {username} display current username

Inspired by i3 FAQ:
    https://faq.i3wm.org/question/1618/add-user-name-to-status-bar.1.html

@author ultrabug

SAMPLE OUTPUT
{'full_text': u'ultrabug'}
"""

from getpass import getuser


class Py3status:
    """
    """

    # available configuration parameters
    format = "{username}"

    class Meta:
        deprecated = {
            "remove": [{"param": "cache_timeout", "msg": "obsolete parameter"}]
        }

    def whoami(self):
        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, {"username": getuser()}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
