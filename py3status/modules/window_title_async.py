"""
Display the current window title with async update.

Uses asynchronous update via i3 IPC events.
Provides instant title update only when it required.

Configuration parameters:
    - format : format of the title, default: "{title}".
    - empty_title : string that will be shown instead of the title
                    when the title is hidden, default: " ".
    - always_show : do not hide the title when it can be already
                    visible (e.g. in tabbed layout), default: False.

Requires:
    - i3ipc (https://github.com/acrisci/i3ipc-python)

@author Anon1234 https://github.com/Anon1234
@license BSD
"""

from threading import Thread

import i3ipc


class Py3status:

    format = "{title}"
    empty_title = " "
    always_show = False

    def __init__(self):
        self.title = self.empty_title

        # we are listening to i3 events in a separate thread
        t = Thread(target=self._loop)
        t.daemon = True
        t.start()

    def _loop(self):

        def get_title(conn):
            tree = conn.get_tree()
            w = tree.find_focused()
            p = w.parent

            # dont show window title when the window already has means
            # to display it
            if not self.always_show and (w.border == "normal" or
                    (p.layout in ("stacked", "tabbed") and len(p.nodes) > 1)):
                return self.empty_title
            else:
                return w.name

        def update_title(conn, e):

            # catch only focused window title updates
            title_changed = hasattr(e, "container") and e.container.focused

            # check if we need to update title due to changes
            # in the workspace layout
            layout_changed = (hasattr(e, "binding") and (
                                e.binding.command.startswith("layout") or
                                e.binding.command.startswith("border")))

            if title_changed or layout_changed:
                self.title = get_title(conn) or self.empty_title

        def clear_title(*args):
            self.title = self.empty_title

        conn = i3ipc.Connection()

        self.title = get_title(conn)  # set title on startup

        # The order of following callbacks is important!

        # clears the title on empty ws
        conn.on('workspace::focus', clear_title)

        # clears the title when the last window on ws was closed
        conn.on("window::close", clear_title)

        # listens for events which can trigger the title update
        conn.on("window::title", update_title)
        conn.on("window::focus", update_title)
        conn.on("binding", update_title)

        conn.main()  # run the event loop

    def window_title(self, i3s_output_list, i3s_config):
        resp = {
            'cached_until': 0,  # update ASAP
            'full_text': self.format.format(title=self.title),
        }

        for option in ('min_width', 'align', 'separator'):
            try:
                resp[option] = getattr(self, option)
            except AttributeError:
                continue

        return resp

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.window_title([], {}))
        sleep(1)
