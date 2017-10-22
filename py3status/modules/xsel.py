# -*- coding: utf-8 -*-
import re
import time
"""
Display X selection.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 0.5)
    command: the clipboard command to run (default 'xsel --output')
    click_command: the clipboard command to run on click
        (default 'xsel --clear --clipboard')
    format: display format for this module (default '{selection}')
    max_size: strip the selection to this value (default 15)
    symmetric: show beginning and end of the selection string
        with respect to configured max_size. (default True)
    log_file: specify the clipboard log to use (default None)

Format placeholders:
    {selection} output from clipboard command

Requires:
    xsel: a command-line program to retrieve/set the X selection

@author Sublim3 umbsublime@gamil.com
@license BSD

SAMPLE OUTPUT
{'full_text': 'selected text'}

example
{'full_text': 'rrrrr > wtf is a warlock doing in here'}
"""


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 0.5
    command = 'xsel --output'
    click_command = 'xsel --clear --clipboard'
    format = '{selection}'
    max_size = 15
    symmetric = True
    log_file = None

    selection_cache = None

    def xsel(self):
        selection = self.py3.command_output(self.command).strip()

        if self.log_file and selection and selection != self.selection_cache:
            with open(self.log_file, "a") as f:
                datetime = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write("{}\n{}\n".format(datetime, selection))
        self.selection_cache = selection

        selection = re.sub(r"\s+", " ", selection)  # merge whitespace into one
        if len(selection) >= self.max_size:
            if self.symmetric is True:
                split = int(self.max_size / 2) - 1
                selection = selection[:split] + '..' + selection[-split:]
            else:
                selection = selection[:self.max_size]
        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'selection': selection})
        }

    def on_click(self, event):
        self.py3.command_output(self.click_command)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
