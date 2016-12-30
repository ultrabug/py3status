# -*- coding: utf-8 -*-
"""
Display the currently logged in user.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 1800)

Inspired by i3 FAQ:
        https://faq.i3wm.org/question/1618/add-user-name-to-status-bar/
"""

from getpass import getuser


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 1800

    def whoami(self):
        """
        We use the getpass module to get the current user.
        """
        # here you can change the format of the output
        # default is just to show the username
        username = '{}'.format(getuser())

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': username
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
