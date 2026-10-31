r"""
Display information about your running terminal multiplexers.

tmux is a terminal multiplexer: it enables a number of terminals to be
created, accessed, and controlled from a single screen. tmux may be detached
from a screen and continue running in the background, then later reattached.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module
        (default '[\?color=session {session}s] {window}w {pane}p')
    format_buffer: display format for buffers (default '{buffer_name}')
    format_buffer_separator: show separator if more than one (default ' ')
    format_client: display format for clients (default '{client_termname}')
    format_client_separator: show separator if more than one (default ' ')
    format_pane: display format for panes (default '{pane_title}')
    format_pane_separator: show separator if more than one (default ' ')
    format_session: display format for sessions (default '{session_name}')
    format_session_separator: show separator if more than one (default ' ')
    format_window: display format for windows (default '{window_name}')
    format_window_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use (default [(0, 'bad'), (1, 'good')])

Format placeholders:
    {buffer}         number of buffers
    {client}         number of clients
    {pane}           number of panes
    {session}        number of sessions
    {window}         number of windows
    {format_buffer}  format for buffers
    {format_client}  format for clients
    {format_pane}    format for panes
    {format_session} format for sessions
    {format_window}  format for windows

format_xxx placeholders:
    See `man -P 'less +/^FORMATS' tmux` for a full list of tmux
    variables to use. Not all tmux variables will be usable.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder, either a
        count in `format` (eg `session`) or a value in `format_xxx`
        (eg `session_windows`, `session_name`)

Examples:
```
# hide when tmux isn't running
tmux {
    format = '[\?if=session [\?color=session {session}s] {window}w {pane}p]'
}

# show window names, with the current window of each session in green
tmux {
    format = '{format_window}'
    format_window = '[\?if=window_active [\?color=good {window_name}]'
    format_window += '|{window_name}]'
    format_window_separator = ', '
}

# show the current window of each session
tmux {
    format = '{format_window}'
    format_window = '[\?if=window_active [\?color=darkgray {session_name}:]'
    format_window += '{window_name}]'
}

# show attached sessions in green, detached ones in yellow
tmux {
    format = '{format_session}'
    format_session = '[\?if=session_attached [\?color=good {session_name}]'
    format_session += '|[\?color=degraded {session_name}]]'
}

# show detached sessions, eg ones you may have forgotten
tmux {
    format = '{format_session}'
    format_session = '[\?if=!session_attached {session_name}]'
}

# show windows that rang the bell, in red
tmux {
    format = '{format_window}'
    format_window = '[\?if=window_bell_flag [\?color=bad '
    format_window += '{session_name}:{window_name}]]'
}

# show zoomed windows, in yellow
tmux {
    format = '{format_window}'
    format_window = '[\?if=window_zoomed_flag [\?color=degraded '
    format_window += '{window_name} (zoomed)]]'
}

# show windows with synchronized panes, in red
tmux {
    format = '{format_window}'
    format_window = '[\?if=pane_synchronized [\?color=bad '
    format_window += '{session_name}:{window_name} sync]]'
}

# show what is running in each window
tmux {
    format = '{format_pane}'
    format_pane = '[\?if=pane_active [\?color=darkgray {window_name}:]'
    format_pane += '{pane_current_command}]'
    format_pane_separator = ', '
}
```

@author lasers

SAMPLE OUTPUT
[{'full_text': '2s', 'color': '#00FF00'}, {'full_text': ' 4w 5p'}]
"""

# fmt: off
STRING_NOT_INSTALLED = "not installed"
NEW_LINE = "|NEWLINE|"
SEPARATOR = "|SEPARATOR|"
IGNORED_TMUX_ERRORS = (
    "no server running", "No such file or directory", "server exited unexpectedly",
)
TEXT = {
    "buffer_full", "buffer_name", "buffer_sample", "client_last_session", "client_session",
    "pane_search_string", "pane_title", "session_group", "session_name", "window_name",
}
COMMANDS = {
    "buffer": "list-buffers", "client": "list-clients", "pane": "list-panes -a",
    "session": "list-sessions", "window": "list-windows -a",
}
# fmt: on


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    format = "[\\?color=session {session}s] {window}w {pane}p"
    format_buffer = "{buffer_name}"
    format_buffer_separator = " "
    format_client = "{client_termname}"
    format_client_separator = " "
    format_pane = "{pane_title}"
    format_pane_separator = " "
    format_session = "{session_name}"
    format_session_separator = " "
    format_window = "{window_name}"
    format_window_separator = " "
    thresholds = [(0, "bad"), (1, "good")]

    def post_config_hook(self):
        if not self.py3.check_commands("tmux"):
            raise Exception(STRING_NOT_INSTALLED)

        self.thresholds_init = {"format": self.py3.get_color_names_list(self.format)}
        placeholders = set(self.py3.get_placeholders_list(self.format))
        placeholders.update(self.thresholds_init["format"])
        self.tmux_queries = {}
        for name, command in COMMANDS.items():
            if not {name, f"format_{name}"} & placeholders:
                continue
            format_string = getattr(self, f"format_{name}")
            self.thresholds_init[name] = self.py3.get_color_names_list(format_string)
            keys = list(
                {*self.py3.get_placeholders_list(format_string), *self.thresholds_init[name]}
            )
            fields = SEPARATOR.join(f"#{{{key}}}" for key in keys)
            self.tmux_queries[name] = {
                "format": format_string,
                "separator": getattr(self, f"format_{name}_separator"),
                "command": f'tmux {command} -F "{fields}{NEW_LINE}"',
                "text": TEXT.intersection(keys),
                "placeholders": keys,
            }

    def _get_rows(self, query):
        try:
            output = self.py3.command_output(query["command"])
        except self.py3.CommandError as err:
            error = (err.error or err.output or str(err)).strip()
            # no server just means nothing to list
            if any(x in error for x in IGNORED_TMUX_ERRORS):
                return []
            self.py3.error(error)
        rows = []
        for line in output.split(NEW_LINE + "\n")[:-1]:
            row = dict(zip(query["placeholders"], line.split(SEPARATOR)))
            for key, value in row.items():
                if value.isdigit() and key not in query["text"]:
                    row[key] = int(value)
            rows.append(row)
        return rows

    def tmux(self):
        tmux_data = {}
        for name, query in self.tmux_queries.items():
            rows = self._get_rows(query)
            new_row = []
            for row in rows:
                for x in self.thresholds_init[name]:
                    if x in row:
                        self.py3.threshold_get_color(row[x], x)
                new_row.append(self.py3.safe_format(query["format"], row))

            format_row_separator = self.py3.safe_format(query["separator"])
            format_row = self.py3.composite_join(format_row_separator, new_row)
            tmux_data.update({name: len(rows), f"format_{name}": format_row})

        for x in self.thresholds_init["format"]:
            if x in tmux_data:
                self.py3.threshold_get_color(tmux_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, tmux_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
