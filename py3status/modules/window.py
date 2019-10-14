# -*- coding: utf-8 -*-
"""
Display window properties (i.e. title, class, instance).

Configuration parameters:
    cache_timeout: refresh interval for i3-msg (default 1)
    format: display format for this module (default '{title}')

Format placeholders:
    {class} window class
    {instance} window instance
    {title} window title

Examples:
```
# show heart instead of empty title
window_title {
    format = '{title}|\u2665'
}

# specify a length
window_title {
    format = '[\?max_length=55 {title}]'
}
```

@author shadowprince (counter), Anon1234 (async)
@license Eclipse Public License (counter), BSD (async)

SAMPLE OUTPUT
{'full_text': u'business_plan_final_3a.doc'}
"""

try:
    import i3ipc
    from threading import Thread

    IPC = "i3ipc"
except Exception:
    IPC = "i3msg"

STRING_ERROR = "invalid ipc `{}`"


class Ipc:
    """
    """

    def __init__(self, parent):
        self.parent = parent

        # deprecations?
        self.max_width = getattr(parent, "max_width", 120)
        self.placeholders = dict.fromkeys(
            self.parent.py3.get_placeholders_list(self.parent.format), ""
        )
        self.placeholders.pop("ipc", None)
        self.setup(parent)

    def set_window_properties(self):
        pass

    def trim_width(self, string):
        if len(string) > self.max_width:
            string = string[: self.max_width - 1] + u"…"
        return string


class I3ipc(Ipc):
    """
    """

    def setup(self, parent):
        self.parent.cache_timeout = self.parent.py3.CACHE_FOREVER
        self.last_window_properties = self.placeholders

        # deprecations?
        self.always_show = getattr(parent, "always_show", False)
        self.empty_title = getattr(parent, "empty_title", "")

        t = Thread(target=self.start)
        t.daemon = True
        t.start()

    def start(self):
        i3 = i3ipc.Connection()
        self.change_title(i3)
        for event in ["workspace::focus", "window::close"]:
            i3.on(event, self.clear_title)
        for event in ["window::title", "window::focus", "binding"]:
            i3.on(event, self.change_title)
        i3.main()

    def clear_title(self, i3, event):
        focused = i3.get_tree().find_focused()
        if not focused.window_class:
            focused.window_title = self.empty_title
        self.update(focused)

    def change_title(self, i3, event=None):
        focused = i3.get_tree().find_focused()

        # do not hide title when it is already visible (e.g. stacked/tabbed layout)
        if not self.always_show and (
            focused.border == "normal"
            or focused.type == "workspace"
            or (
                focused.parent.layout in ("stacked", "tabbed")
                and len(focused.parent.nodes) > 1
            )
        ):
            focused.window_title = self.empty_title
        else:
            # deprecation?
            focused.window_title = self.trim_width(focused.window_title)
        self.update(focused)

    def update(self, window_properties):
        window_properties = {
            "title": window_properties.window_title,
            "class": window_properties.window_class,
            "instance": window_properties.window_instance,
        }
        if window_properties != self.last_window_properties:
            self.last_window_properties = window_properties
            self.parent.window_properties = window_properties
            self.parent.py3.update()


class I3msg(Ipc):
    """
    i3-msg - send messages to i3 window manager
    """

    def setup(self, parent):
        from json import loads as json_loads

        self.json_loads = json_loads
        self.tree_command = [self.parent.py3.get_wm_msg(), "-t", "get_tree"]

    def set_window_properties(self):
        tree = self.json_loads(self.parent.py3.command_output(self.tree_command))
        window_properties = self.find_focused(tree).get(
            "window_properties", self.placeholders
        )
        window_properties["title"] = self.trim_width(window_properties.get("title", ""))
        self.parent.window_properties = {
            x: window_properties.get(x, "") for x in self.placeholders
        }

    def find_focused(self, tree):
        if isinstance(tree, list):
            for el in tree:
                res = self.find_focused(el)
                if res:
                    return res
        elif isinstance(tree, dict):
            if tree["focused"]:
                return tree
            return self.find_focused(tree["nodes"] + tree["floating_nodes"])
        return {}


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 1
    format = "{title}"

    def post_config_hook(self):
        #  ipc: specify i3ipc or i3-msg, otherwise auto (default None)
        self.ipc = getattr(self, "ipc", IPC).replace("-", "")

        self.window_properties = {}
        if self.ipc in ["i3ipc", "i3msg"]:
            if self.ipc == "i3ipc":
                import i3ipc  # noqa f401, raise exception
            self.backend = globals()[self.ipc.capitalize()](self)
        else:
            raise Exception(STRING_ERROR.format(self.ipc))

    def _get_window_properties(self):
        self.backend.set_window_properties()
        return self.window_properties

    def window(self):
        window_properties = self._get_window_properties()

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, window_properties),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    config = {"format": "\[{ipc}\] {title}"}
    module_test(Py3status, config=config)
