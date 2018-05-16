# -*- coding: utf-8 -*-
"""
Display number of scratchpad windows and urgency hints.

Configuration parameters:
    cache_timeout: refresh interval for i3-msg (default 5)
    format: display format for this module
        (default "\u232b [\?color=scratchpad {scratchpad}]")
    thresholds: specify color thresholds to use
        (default [(0, "darkgray"), (1, "violet")])

Format placeholders:
    {scratchpad} number of scratchpads
    {urgent} number of urgent scratchpads

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Optional:
    i3ipc: an improved python library to control i3wm (async)
    i3-msg: send messages to i3 window manager (counter)

Examples:
```
# hide zero scratchpad
scrathpad {
    format = '[\?not_zero \u232b [\?color=scratchpad {scratchpad}]]'
}

# show urgent scratchpads
scrathpad {
    format = '[\?not_zero \u232b {urgent}]'
}

# bring up scratchpads on clicks
scratchpad {
    on_click 1 = 'scratchpad show'
}
```

@author shadowprince (counter), cornerman (async)
@license Eclipse Public License (counter), BSD (async)

SAMPLE OUTPUT
[{'full_text': '\u232b '}, {'full_text': u'0', 'color': '#a9a9a9'}]

violet
[{'full_text': '\u232b '}, {'full_text': u'5', 'color': '#ee82ee'}]

urgent
{'full_text': '\u232b URGENT 1', 'urgent': True}
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
        self.setup(parent)

    def set_scratchpad_leaves(self):
        pass


class I3ipc(Ipc):
    """
    i3ipc - an improved python library to control i3wm
    """

    def setup(self, parent):
        self.parent.cache_timeout = self.parent.py3.CACHE_FOREVER
        t = Thread(target=self.start)
        t.daemon = True
        t.start()

    def start(self):
        i3 = i3ipc.Connection()
        self.update(i3)
        for event in ["window::move", "window::urgent"]:
            i3.on(event, self.update)
        i3.main()

    def update(self, i3, event=None):
        leaves = i3.get_tree().scratchpad().leaves()
        self.parent.leaves = [window.urgent for window in leaves]
        self.parent.py3.update()


class I3msg(Ipc):
    """
    i3-msg - send messages to i3 window manager
    """

    def setup(self, parent):
        from json import loads

        self.json_loads = loads
        self.tree_command = [self.parent.py3.get_wm_msg(), "-t", "get_tree"]

    def set_scratchpad_leaves(self):
        tree = self.parent.py3.command_output(self.tree_command)
        leaves = self.find_scratchpad(self.json_loads(tree)).get("floating_nodes", [])
        self.parent.leaves = [window["urgent"] for window in leaves]

    def find_scratchpad(self, tree):
        if tree.get("name") == "__i3_scratch":
            return tree
        for x in tree.get("nodes", []):
            result = self.find_scratchpad(x)
            if result:
                return result
        return {}


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = "\u232b [\?color=scratchpad {scratchpad}]"
    thresholds = [(0, "darkgray"), (1, "violet")]

    def post_config_hook(self):
        # ipc: specify i3ipc or i3-msg, otherwise auto (default None)
        self.ipc = getattr(self, "ipc", IPC).replace("-", "")

        self.leaves = []
        if self.ipc in ["i3ipc", "i3msg"]:
            if self.ipc == "i3ipc":
                import i3ipc  # noqa f401, raise exception
            self.backend = globals()[self.ipc.capitalize()](self)
        else:
            raise Exception(STRING_ERROR.format(self.ipc))

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def _get_scratchpad_leaves(self):
        self.backend.set_scratchpad_leaves()
        return self.leaves

    def scratchpad(self):
        scratchpad_leaves = self._get_scratchpad_leaves()

        scratchpad_data = {
            "ipc": self.ipc,
            "scratchpad": len(scratchpad_leaves),
            "urgent": sum(scratchpad_leaves),
        }

        for x in self.thresholds_init:
            if x in scratchpad_data:
                self.py3.threshold_get_color(scratchpad_data[x], x)

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, scratchpad_data),
        }
        if scratchpad_data["urgent"]:
            response["urgent"] = True
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    format = "\[{ipc}\] [\?color=scratchpad {scratchpad}]"

    module_test(Py3status, config={"format": format})
