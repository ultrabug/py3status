# -*- coding: utf-8 -*-
"""
Display X selection.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 0.5)
    command: the xsel command to run (default 'xsel -o')
    max_size: stip the selection to this value (default 15)
    symmetric: show the beginning and the end of the selection string
        with respect to configured max_size. (default True)

Requires:
    xsel: command line tool

@author Sublim3 umbsublime@gamil.com
@license BSD
"""


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 0.5
    command = 'xsel -o'
    max_size = 15
    symmetric = True

    def xsel(self):
        """
        Display the content of xsel.
        """
        output = self.py3.command_output(self.command)
        if len(output) >= self.max_size:
            if self.symmetric is True:
                split = int(self.max_size / 2) - 1
                output = output[:split] + '..' + output[-split:]
            else:
                output = output[:self.max_size]
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': output,
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
