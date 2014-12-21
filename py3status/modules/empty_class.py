# -*- coding: utf-8 -*-
"""
Empty and basic py3status class.

NOTE: py3status will NOT execute:
    - methods starting with '_'
    - methods decorated by @property and @staticmethod

NOTE: reserved method names:
    - 'kill' method for py3status exit notification
    - 'on_click' method for click events from i3bar (read below please)
"""

# import your useful libs here
from time import time


class Py3status:
    """
    The Py3status class name is mendatory.

    Below you list all the available configuration parameters and their
    default value for your module which can be overwritten by users
    directly from their i3status config.

    This examples features only one parameter which is 'cache_timeout'
    and is set to 10 seconds (0 would mean no cache).
    """

    # available configuration parameters
    cache_timeout = 10

    def __init__(self):
        """
        This is the class constructor which will be executed once.
        """
        pass

    def kill(self, i3s_output_list, i3s_config):
        """
        This method will be called upon py3status exit.
        """
        pass

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        This method should only be used for ADVANCED and very specific usages.

        Read the 'Handle click events directly from your i3status config'
        article from the py3status wiki:
            https://github.com/ultrabug/py3status/wiki/

        This method will be called when a click event occurs on this module's
        output on the i3bar.

        Example 'event' json object:
        {'y': 13, 'x': 1737, 'button': 1, 'name': 'empty', 'instance': 'first'}
        """
        pass

    def empty(self, i3s_output_list, i3s_config):
        """
        This method will return an empty text message
        so it will NOT be displayed on your i3bar.

        If you want something displayed you should write something
        in the 'full_text' key of your response.

        See the i3bar protocol spec for more information:
        http://i3wm.org/docs/i3bar-protocol.html
        """
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.empty([], {}))
        sleep(1)
