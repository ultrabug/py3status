# -*- coding: utf-8 -*-
"""
Cache output of a long-running script, display it on click in a notification.

Configuration parameters:
    button_refresh: mouse button to refresh this module
        (default 3)
    button_show_notification: mouse button to show last output in a notification
        (default 1)
    cache_timeout: how often we refresh this module in seconds
        (default 600)
    format: see placeholders below
        (default '{first_line}')
    localize: should script output be localized (if available)
        (default True)
    script_path: script you want to execute (required parameter)
        (default None)

Format placeholders:
    {first_line} first line of the output of the script
    {n_lines} number of lines in the output of the script

i3status.conf example:

```
cached_script {
    format = "my name is {first_line}"
    script_path = "/usr/bin/whoami"
}
```

@author Maxim Baz

SAMPLE OUTPUT
{'full_text': 'script output'}

example
{'full_text': 'It is now: Wed Feb 22 22:24:13'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    button_refresh = 3
    button_show_notification = 1
    cache_timeout = 600
    format = "{first_line}"
    localize = True
    script_path = None

    def post_config_hook(self):
        if not self.script_path:
            raise Exception("missing 'script_path' parameter")

    def cached_script(self):
        response = {}
        response["cached_until"] = self.py3.time_in(self.cache_timeout)
        try:
            self.last_output = self.py3.command_output(
                self.script_path, shell=True, localized=self.localize
            )
        except self.py3.CommandError as e:
            error = e.output or e.error
            self.py3.error("error: " + error)

        output_lines = self.last_output.splitlines()
        n_lines = len(output_lines)
        first_line = output_lines[0] if n_lines > 0 else ""
        response["full_text"] = self.py3.safe_format(
            self.format, {"first_line": first_line, "n_lines": n_lines}
        )
        return response

    def on_click(self, event):
        button = event["button"]
        if button == self.button_show_notification:
            self.py3.notify_user(self.last_output)
        if button != self.button_refresh:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
