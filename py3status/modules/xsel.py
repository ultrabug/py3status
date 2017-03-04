# -*- coding: utf-8 -*-
"""
Display X selection.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 0.5)
    command: the clipboard command to run (default 'xsel -o')
    format: display format for this module (default '{output}')
    max_size: strip the selection to this value (default 15)
    symmetric: show beginning and end of the selection string
        with respect to configured max_size. (default True)

Requires:
    xsel: a command-line program to retrieve/set the X selection

@author Sublim3 umbsublime@gamil.com
@license BSD
"""


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 0.5
    command = 'xsel -o'
    format = '{output}'
    max_size = 15
    symmetric = True

    def xsel(self):
        output = self.py3.command_output(self.command)
        output = output.splitlines()[0]
        if len(output) >= self.max_size:
            if self.symmetric is True:
                split = int(self.max_size / 2) - 1
                output = output[:split] + '..' + output[-split:]
            else:
                output = output[:self.max_size]
        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'output': output})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
