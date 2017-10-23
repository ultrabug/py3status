# -*- coding: utf-8 -*-
import time
import os
"""
Display X selection.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 0.5)
    command: the clipboard command to run (default 'xsel --output')
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

Example:
xsel {
  max_size = 50
  command = "xsel --clipboard --output"
  on_click 1 = "exec xsel --clear --clipboard"
  log_file = "~/.local/share/xsel/clipboard_log"
}
"""


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 0.5
    command = 'xsel --output'
    format = '{selection}'
    max_size = 15
    symmetric = True
    log_file = None

    def post_config_hook(self):
        self.selection_cache = None
        self.log_file = os.path.expanduser(self.log_file)

    def xsel(self):
        selection = self.py3.command_output(self.command).strip()

        if self.log_file and selection and selection != self.selection_cache:
            with open(self.log_file, "a") as f:
                datetime = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write("{}\n{}\n".format(datetime, selection))
        self.selection_cache = selection

        selection = ' '.join(selection.split())
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


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
