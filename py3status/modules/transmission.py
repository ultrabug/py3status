r"""
Display number of torrents and more.

Configuration parameters:
    arguments: additional arguments for the transmission-remote (default None)
    button_next: mouse button to switch next torrent (default None)
    button_previous: mouse button to switch previous torrent (default None)
    button_run: mouse button to run the command on current torrent
        (default [(1, '--start'), (2, '--verify'), (3, '--stop')])
    cache_timeout: refresh interval for this module (default 20)
    format: display format for this module (default '{format_torrent}')
    format_separator: show separator if more than one (default ' ')
    format_torrent: display format for torrents
        (default '[\?if=is_focused&color=bad X] {status} {id} {name} {done}%')
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {torrent} number of torrents
    {format_torrent} format for torrents
    {up} summary up traffic
    {down} summary down traffic
    {have} summary download

format_torrent placeholders:
    {index} torrent index, eg 1
    {id} torrent id, eg 2
    {done} torrent percent, eg 100%
    {have} torrent download, 253 KB
    {eta} torrent estimated time, eg Done, 1 min, etc
    {up} torrent up traffic
    {down} torrent down traffic
    {ratio} torrent seed ratio
    {status} torrent status, eg Idle, Downloading, Stopped, Verifying, etc
    {name} torrent name, eg py3status-3.8.tar.gz

Color options:
    color_bad: current torrent

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    transmission-cli:
        fast, easy, and free bittorrent client (cli tools, daemon, web client)

Examples:
```
# add arguments
transmission {
    # We use 'transmission-remote --list'
    # See `transmission-remote --help' for more information.
    # Not all of the arguments will work here.
    arguments = '--auth username:password --port 9091'
}
# see 'man transmission-remote' for more buttons
transmission {
    button_run = [
        (1, '--start'),
        (2, '--verify'),
        (3, '--stop'),
        (8, '--remove'),
        (9, '--exit'),
    ]
}

# open web-based transmission client
transmission {
    on_click 1 = 'exec xdg-open http://username:password@localhost:9091'
}

# add buttons
transmission {
    button_next = 5
    button_previous = 4
}

# see 'man transmission-remote' for more buttons
transmission {
    # specify a script to run when a torrent finishes
    on_click 9 = 'exec transmission-remote --torrent-done-script ~/file'

    # use the alternate limits?
    on_click 9 = 'exec transmission-remote --alt-speed'
    on_click 10 = 'exec transmission-remote --no-alt-speed'
}

# show summary statistcs - up, down, have
transmission {
    format = '{format_torrent}'
    format += '[\?color=#ffccff [\?not_zero  Up:{up}]'
    format += '[\?not_zero  Down:{down}][\?not_zero  Have:{have}]]'
}

# add a format that sucks less than the default plain format
transmission {
    format_torrent = '[\?if=is_focused&color=bad X ]'
    format_torrent += '[[\?if=status=Idle&color=degraded {status}]'
    format_torrent += '|[\?if=status=Stopped&color=bad {status}]'
    format_torrent += '|[\?if=status=Downloading&color=good {status}]'
    format_torrent += '|[\?if=status=Verifying&color=good {status}]'
    format_torrent += '|\?color=degraded {status}]'
    format_torrent += ' {name} [\?color=done {done}]'
}

# show percent thresholds
transmission {
    format_torrent = '{name} [\?color=done {done}]'
    thresholds = [(0, 'bad'), (1, 'degraded'), (100, 'good')]
}

# download the rainbow
transmission {
    format_torrent = '[\?if=is_focused&color=bad X ]'
    format_torrent += '{status} [\?color=index {name}] [\?color=done {done}%]'
    thresholds = {
        'done': [(0, '#ffb3ba'), (1, '#ffffba'), (100, '#baefba')],
        'index': [
            (1, '#ffb3ba'), (2, '#ffdfba'), (3, '#ffffba'),
            (4, '#baefba'), (5, '#baffc9'), (6, '#bae1ff'),
            (7, '#bab3ff')
        ]
    }
}
```

@author lasers

SAMPLE OUTPUT
{'full_text': 'Downloading py3status-3.8.tar.gz 89%'}

verifying
{'full_text': 'Verifying py3status-3.8.tar.gz 100%'}

stopped
{'full_text': 'Stopped py3status-3.8.tar.gz 100%'}

idle
{'full_text': 'Idle py3status-3.8.tar.gz 100%'}

"""

import time

STRING_NOT_INSTALLED = "transmission-remote not installed"


class Py3status:
    """
    """

    # available configuration parameters
    arguments = None
    button_next = None
    button_previous = None
    button_run = [(1, "--start"), (2, "--verify"), (3, "--stop")]
    cache_timeout = 20
    format = "{format_torrent}"
    format_separator = " "
    format_torrent = r"[\?if=is_focused&color=bad X] {status} {id} {name} {done}%"
    thresholds = []

    def post_config_hook(self):
        self.command = "transmission-remote --list"
        if not self.py3.check_commands(self.command):
            raise Exception(STRING_NOT_INSTALLED)
        if self.arguments:
            self.command = f"{self.command} {self.arguments}"
        self.init_summary = self.py3.format_contains(
            self.format, ["up", "down", "have"]
        )
        self.id = 0
        self.state = None
        self.reset_id = self.id
        self.torrent_data = None
        self.is_scrolling = False
        self.count_torrent = 0
        self.summary_data = {}

        self.thresholds_init = {}
        for name in ["format", "format_torrent"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def _scroll(self, direction=0):
        self.is_scrolling = True
        data = self.shared
        if direction == 0:
            self.id = self.reset_id
            self.state = None
            self.is_scrolling = False
            for d in data:
                d["is_focused"] = False
        else:
            if data and not any(d for d in data if d["is_focused"]):
                data[0]["is_focused"] = True

            length = len(data)
            for index, d in enumerate(data):
                if d.get("is_focused"):
                    data[index]["is_focused"] = False
                    if direction < 0:  # switch previous
                        if index > 0:
                            data[index - 1]["is_focused"] = True
                        else:
                            data[index]["is_focused"] = True
                    elif direction > 0:  # switch next
                        if index < (length - 1):
                            data[index + 1]["is_focused"] = True
                        else:
                            data[length - 1]["is_focused"] = True
                    break

            for d in data:
                if d["is_focused"]:
                    self.id = d["id"]
                    self.state = d["status"]
                    break

        self._manipulate(data)

    def _organize(self, data):
        self.id = self.reset_id
        new_data = []
        for line in data:
            new_data.append(
                {
                    "is_focused": None,
                    "id": line[0:6].strip(),
                    "done": line[7:12].strip().strip("%"),
                    "have": line[13:23].strip(),
                    "eta": line[24:33].strip(),
                    "up": line[34:41].strip(),
                    "down": line[42:49].strip(),
                    "ratio": line[50:56].strip(),
                    "status": line[57:69].strip(),
                    "name": line[70:].strip(),
                }
            )
        return new_data

    def _manipulate(self, data):
        self.shared = data
        new_data = []
        for index, t in enumerate(data, 1):
            t["index"] = index
            if not self.is_scrolling:
                t["is_focused"] = False
            for x in self.thresholds_init["format_torrent"]:
                if x in t:
                    self.py3.threshold_get_color(t[x], x)

            new_data.append(self.py3.safe_format(self.format_torrent, t))
        return new_data

    def transmission(self):
        data = self.torrent_data
        summary_data = self.summary_data

        if not self.is_scrolling:
            data = self.py3.command_output(self.command).splitlines()
            if self.init_summary:
                summary_line = data[-1]
                summary_data["have"] = summary_line[13:23].strip()
                summary_data["up"] = summary_line[34:41].strip()
                summary_data["down"] = summary_line[42:49].strip()
            data = data[1:-1]
            self.count_torrent = len(data)
            data = self.torrent_data = self._organize(data)

        data = self._manipulate(data)
        format_separator = self.py3.safe_format(self.format_separator)
        format_torrent = self.py3.composite_join(format_separator, data)

        summary_data.update(
            {"torrent": self.count_torrent, "format_torrent": format_torrent}
        )

        for x in self.thresholds_init["format"]:
            if x in summary_data:
                self.py3.threshold_get_color(summary_data[x], x)

        self.is_scrolling = False
        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, summary_data),
        }

    def on_click(self, event):
        button = event["button"]
        self.id = str(self.id).strip("*")
        if button == self.button_next and self.torrent_data:
            self._scroll(+1)
        elif button == self.button_previous and self.torrent_data:
            self._scroll(-1)
        elif self.id:
            for x in self.button_run:
                if button == x[0]:
                    cmd = "transmission-remote -t {} {}".format(self.id, x[1])
                    self.py3.command_run(cmd)
                    time.sleep(0.75)
                    break


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
