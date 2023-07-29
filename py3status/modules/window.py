"""
Display window properties (i.e. title, class, instance).

Configuration parameters:
    cache_timeout: refresh interval for i3-msg or swaymsg (default 0.5)
    format: display format for this module (default "{title}")
    hide_title: hide title on containers with window title (default False)
    max_width: specify width to truncate title with ellipsis (default None)

Format placeholders:
    {class} window class
    {instance} window instance
    {title} window title

Requires:
    i3ipc: an improved python library to control i3wm and sway

Examples:
```
# show alternative instead of empty title
window_title {
    format = '{title}|\u2665'
}
```

@author shadowprince (counter), Anon1234 (async)
@license Eclipse Public License (counter), BSD (async)

SAMPLE OUTPUT
{'full_text': u'scary snake movie - mpv'}

ellipsis
{'full_text': u'GitHub - ultrabug/py3sta…'}
"""

STRING_ERROR = "invalid ipc `{}`"


class Ipc:
    """ """

    def __init__(self, parent):
        self.parent = parent
        self.setup(parent)

    def compatibility(self, window_properties):
        # specify width to truncate title with ellipsis
        title = window_properties.get("title", "")
        if title:
            if self.parent.max_width and len(title) > self.parent.max_width:
                window_properties["title"] = title[: self.parent.max_width - 1] + "…"
        else:
            window_properties["title"] = ""

        return window_properties


class I3ipc(Ipc):
    """
    i3ipc - an improved python library to control i3wm and sway
    """

    _focused_workspace = None
    _focused_window = None

    def setup(self, parent):
        from threading import Thread

        self.parent.cache_timeout = self.parent.py3.CACHE_FOREVER
        self.window_properties = {}

        t = Thread(target=self.start)
        t.daemon = True
        t.start()

    # noinspection PyTypeChecker
    def start(self):
        from i3ipc import Connection, Event

        self.i3 = Connection()

        self._update(self.i3.get_tree().find_focused())

        self.i3.on(Event.WORKSPACE_FOCUS, self._on_workplace_focus)
        self.i3.on(Event.WINDOW_CLOSE, self._on_window_close)
        self.i3.on(Event.WINDOW_TITLE, self._on_window_title)
        self.i3.on(Event.WINDOW_FOCUS, self._on_window_focus)
        self.i3.on(Event.BINDING, self._on_binding)
        self.i3.main()

    def _on_workplace_focus(self, i3, event):
        self._focused_workspace = event.current
        self._focused_window = None
        if event.current.nodes or event.current.floating_nodes:
            return
        self._update(event.current)

    def _on_window_close(self, i3, event):
        if event.container.window == self._focused_window:
            self._focused_window = None
            self._update(i3.get_tree().find_focused())

    def _on_binding(self, i3, event):
        self._update(i3.get_tree().find_focused())

    def _on_window_title(self, i3, event):
        if event.container.focused:
            self._update(event.container)

    def _on_window_focus(self, i3, event):
        self._focused_window = event.container.window
        self._update(event.container)

    def _update(self, event_element):
        if not event_element:
            return

        # hide title on containers with window title
        if self.parent.hide_title:
            show_name = True
            if event_element.border == "normal" or event_element.type == "workspace":
                show_name = False
            else:
                event_element_parent = event_element.parent or getattr(
                    self.i3.get_tree().find_by_id(event_element.id), "parent", None
                )
                if (
                    event_element_parent
                    and event_element_parent.layout in ("stacked", "tabbed")
                    and len(event_element_parent.nodes) > 1
                ):
                    show_name = False

            window_properties = {
                "title": event_element.name if show_name else None,
                "class": event_element.window_class,
                "instance": event_element.window_instance,
            }

        else:
            window_properties = {
                "title": event_element.name,
                "class": event_element.window_class,
                "instance": event_element.window_instance,
            }

        window_properties = self.compatibility(window_properties)

        if self.window_properties != window_properties:
            self.window_properties = window_properties
            self.parent.py3.update()

    def get_window_properties(self):
        return self.window_properties


class Msg(Ipc):
    """
    i3-msg - send messages to i3 window manager
    swaymsg - send messages to sway window manager
    """

    def setup(self, parent):
        from json import loads as json_loads

        self.json_loads = json_loads
        wm_msg = {"i3msg": "i3-msg"}.get(parent.ipc, parent.ipc)
        self.tree_command = [wm_msg, "-t", "get_tree"]

    def get_window_properties(self):
        tree = self.json_loads(self.parent.py3.command_output(self.tree_command))
        focused = self.find_needle(tree)
        window_properties = focused.get(
            "window_properties", {"title": None, "class": None, "instance": None}
        )

        # hide title on containers with window title
        if self.parent.hide_title:
            parent = self.find_needle(tree, focused)
            if (
                focused["border"] == "normal"
                or focused["type"] == "workspace"
                or (parent["layout"] in ("stacked", "tabbed") and len(parent["nodes"]) > 1)
            ):
                window_properties["title"] = None
        window_properties = self.compatibility(window_properties)
        return window_properties

    def find_needle(self, tree, focused=None):
        if isinstance(tree, list):
            for el in tree:
                res = self.find_needle(el, focused)
                if res:
                    return res
        elif isinstance(tree, dict):
            nodes = tree.get("nodes", []) + tree.get("floating_nodes", [])
            if focused:
                for node in nodes:
                    if node["id"] == focused["id"]:
                        return tree
            elif tree["focused"]:
                return tree
            return self.find_needle(nodes, focused)
        return {}


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 0.5
    format = "{title}"
    hide_title = False
    max_width = None

    def post_config_hook(self):
        # ipc: specify i3ipc, i3-msg, or swaymsg, otherwise auto
        self.ipc = getattr(self, "ipc", "")
        if self.ipc in ["", "i3ipc"]:
            try:
                from i3ipc import Connection  # noqa f401, auto ipc

                self.ipc = "i3ipc"
            except Exception:
                if self.ipc:
                    raise  # module not found

        self.ipc = (self.ipc or self.py3.get_wm_msg()).replace("-", "")
        if self.ipc in ["i3ipc"]:
            self.backend = I3ipc(self)
        elif self.ipc in ["i3msg", "swaymsg"]:
            self.backend = Msg(self)
        else:
            raise Exception(STRING_ERROR.format(self.ipc))

    def window(self):
        window_properties = self.backend.get_window_properties()

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, window_properties),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    config = {"format": r"\[{ipc}\] [\?color=pink {title}]"}
    module_test(Py3status, config=config)
