# -*- coding: utf-8 -*-
"""
Simply output the currently logged in user in i3bar.

Inspired by i3 FAQ:
    https://faq.i3wm.org/question/1618/add-user-name-to-status-bar/
"""

from getpass import getuser
from time import time


class Py3status:

    # available configuration parameters
    cache_timeout = 1800

    def whoami(self, i3s_output_list, i3s_config):
        """
        We use the getpass module to get the current user.
        """
        # here you can change the format of the output
        # default is just to show the username
        username = '{}'.format(getuser())

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': username
        }
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.whoami([], {}))
        sleep(1)
