# -*- coding: utf-8 -*-
"""
Display number of scratchpad windows and urgency hints.

Configuration parameters:
    cache_timeout: refresh interval for i3-msg or swaymsg (default 5)
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
    i3ipc: an improved python library to control i3wm and sway

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
[{'full_text': '\u232b URGENT 1', 'urgent': True}]
"""

STRING_ERROR = "invalid ipc `{}`"


class Ipc:
    """
    """

    def __init__(self, parent):
        self.parent = parent
        self.setup(parent)


class I3ipc(Ipc):
    """
    i3ipc - an improved python library to control i3wm and sway
    """

    def setup(self, parent):
        from threading import Thread

        self.parent.cache_timeout = self.parent.py3.CACHE_FOREVER
        self.nodes = []

        t = Thread(target=self.start)
        t.daemon = True
        t.start()

    def start(self):
        from i3ipc import Connection

        i3 = Connection()
        self.update(i3)
        for event in ["window::move", "window::urgent"]:
            i3.on(event, self.update)
        i3.main()

    def update(self, i3, event=None):
        self.nodes = i3.get_tree().scratchpad().leaves()
        self.parent.py3.update()

    def get_scratchpad_nodes(self):
        return [window.urgent for window in self.nodes]


class Msg(Ipc):
    """
    i3-msg - send messages to i3 window manager
    swaymsg - send messages to sway window manager
    """

    def setup(self, parent):
        from json import loads

        self.json_loads = loads
        wm_msg = {"i3msg": "i3-msg"}.get(parent.ipc, parent.ipc)
        self.tree_command = [wm_msg, "-t", "get_tree"]

    def get_scratchpad_nodes(self):
        tree = self.json_loads(self.parent.py3.command_output(self.tree_command))
        nodes = self.find_scratchpad(tree).get("floating_nodes", [])
        return [window["urgent"] for window in nodes]

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
        # ipc: specify i3ipc, i3-msg, or swaymsg, otherwise auto (default None)
        self.ipc = getattr(self, "ipc", "").replace("-", "")
        if self.ipc in ["", "i3ipc"]:
            try:
                from i3ipc import Connection  # noqa f401

                self.ipc = "i3ipc"
            except Exception:
                if self.ipc:
                    raise  # module not found

        self.ipc = self.ipc or self.py3.get_wm_msg().replace("-", "")
        if self.ipc in ["i3ipc"]:
            self.backend = I3ipc(self)
        elif self.ipc in ["i3msg", "swaymsg"]:
            self.backend = Msg(self)
        else:
            raise Exception(STRING_ERROR.format(self.ipc))

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def scratchpad(self):
        scratchpad_nodes = self.backend.get_scratchpad_nodes()

        scratchpad_data = {
            "ipc": self.ipc,
            "scratchpad": len(scratchpad_nodes),
            "urgent": sum(scratchpad_nodes),
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

    config = {"format": "\[{ipc}\] [\?color=scratchpad {scratchpad}]"}

    module_test(Py3status, config=config)
