# This is an example module to be used as a template.
# See https://github.com/ultrabug/py3status/wiki/Write-your-own-modules
# for more details.
#
# NOTE: py3status will NOT execute:
#     - methods starting with '_'
#     - methods decorated by @property and @staticmethod
#
# NOTE: reserved method names:
#     - 'kill' method for py3status exit notification
#     - 'on_click' method for click events from i3bar (read below please)
#
# WARNING:
#
# Do NOT use print on your modules: py3status will catch any output and discard
# it silently because this would break your i3bar (see issue #20 for details).
# Make sure you catch any output from any external program you may call
# from your module. Any output from an external program cannot be caught and
# silenced by py3status and will break your i3bar so please, redirect any
# stdout/stderr to /dev/null for example (see issue #20 for details).
#
# CONTRIBUTORS:
#
# Contributors are kindly requested to agree to contribute their code under
# the BSD license to match py3status' one.
#
# Any contributor to this module should add his/her name to the @author
# line, comma separated.
#
# DOCSTRING:
#
# Fill in the following docstring: it will be parsed by py3status to document
# your module from the CLI.  Please follow the example below.
"""
One-line summary followed by an empty line.

Multi-line description followed by an empty line.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds
        (default 10)
    format: Format for module output (default "{output}")

Format of status string placeholders:
    {output} output of this module

@author <your full name> <your email address>
@license BSD
"""

# import your useful libs here
from time import time


class Py3status:
    """
    The Py3status class name is mandatory.

    Below you list all the available configuration parameters and their
    default value for your module which can be overwritten by users
    directly from their i3status config.

    This examples features only two parameters:
    'cache_timeout' is set to 10 seconds (0 would mean no cache).
    'format' this allows users to customise their output.  In this example we
    have a status string placeholder.  This will be replaced by the module.
    Some modules have multiple placeholders.  For examples look at the included
    py3status modules.
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{output}"

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
        {'y': 13, 'x': 17, 'button': 1, 'name': 'example', 'instance': 'first'}
        """
        pass

    def example_method(self, i3s_output_list, i3s_config):
        """
        This method will return an empty text message
        so it will NOT be displayed on your i3bar.

        If you want something displayed you should write something
        in the 'full_text' key of your response.

        See the i3bar protocol spec for more information:
        http://i3wm.org/docs/i3bar-protocol.html
        """
        # create out output text replacing the placeholder
        full_text = self.format.format(output="example")
        response = {"cached_until": time() + self.cache_timeout, "full_text": full_text}
        return response


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    This SHOULD work before contributing your module please.
    """
    from time import sleep

    x = Py3status()
    config = {
        "color_bad": "#FF0000",
        "color_degraded": "#FFFF00",
        "color_good": "#00FF00",
    }
    while True:
        print(x.example_method([], config))
        sleep(1)
