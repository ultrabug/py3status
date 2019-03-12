# -*- coding: utf-8 -*-
"""
Display number of windows in scratchpad.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 5)
    format: Format of indicator (default '{counter} ⌫')
    hide_when_none: Hide indicator when there is no windows (default False)

Format placeholders:
    {counter} number of scratchpad windows

@author shadowprince
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': '2 ⌫'}
"""

from json import loads


def find_scratch(tree):
    if tree.get("name") == "__i3_scratch":
        return tree
    else:
        for x in tree.get("nodes", []):
            result = find_scratch(x)
            if result:
                return result
    return {}


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = u"{counter} ⌫"
    hide_when_none = False

    class Meta:
        deprecated = {
            "format_fix_unnamed_param": [
                {
                    "param": "format",
                    "placeholder": "counter",
                    "msg": "{} should not be used in format use `{counter}`",
                }
            ]
        }

    def post_config_hook(self):
        self.tree_command = "{} -t get_tree".format(self.py3.get_wm_msg())

    def scratchpad_counter(self):
        tree = loads(self.py3.command_output(self.tree_command))
        count = len(find_scratch(tree).get("floating_nodes", []))

        response = {"cached_until": self.py3.time_in(self.cache_timeout)}

        if self.hide_when_none and count == 0:
            response["full_text"] = ""
        else:
            response["full_text"] = self.py3.safe_format(
                self.format, {"counter": count}
            )

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
