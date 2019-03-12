# -*- coding: utf-8 -*-
"""
Display window title.

This module prints the properties of a focused window at frequent intervals.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 0.5)
    format: display format for this module (default '{title}')
    max_width: If width of title is greater, shrink it and add '...'
        (default 120)

Format placeholders:
    {class} class name
    {instance} instance name
    {title} title name

Examples:
```
# show heart if no title
window_title {
    format = '{title}|\u2665'
}

# specify a length
window_title {
    format = '[\?max_length=55 {title}]'
}
```

@author shadowprince
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': u'business_plan_final_3a.doc'}
"""

from json import loads


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 0.5
    format = "{title}"
    max_width = 120

    def post_config_hook(self):
        self.tree_command = "{} -t get_tree".format(self.py3.get_wm_msg())
        # empty defaults to replace window properties
        self.empty_defaults = {
            x: "" for x in self.py3.get_placeholders_list(self.format)
        }

    def _find_focused(self, tree):
        if isinstance(tree, list):
            for el in tree:
                res = self._find_focused(el)
                if res:
                    return res
        elif isinstance(tree, dict):
            if tree["focused"]:
                return tree
            return self._find_focused(tree["nodes"] + tree["floating_nodes"])
        return {}

    def window_title(self):
        tree = loads(self.py3.command_output(self.tree_command))
        window_properties = self._find_focused(tree).get(
            "window_properties", self.empty_defaults
        )

        if len(window_properties.get("title", "")) > self.max_width:
            window_properties["title"] = u"...{}".format(
                window_properties["title"][-(self.max_width - 3) :]
            )

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, window_properties),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
