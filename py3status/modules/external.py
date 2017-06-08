# -*- coding: utf-8 -*-
"""
Display output from external command, script, program, etc.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 60)
    command: external command, script, program, etc to use
        (default None)
    format: display format for external module
        (default '{output}')
    hide_warning: hide warning about too many newlines
        (default False)
    max_width: limit the output width to this value
        (default -1)
    msg_separator: string for separator
        (default '...')
    msg_warning: string for warning message
        (default 'external: too many newlines')
    strip_whitespace: remove the leading and trailing whitespace
        (default False)
    symmetric: show the beginning and the end of the selection string
        with respect to configured max_width.
        (default False)

Format placeholders:
    {output} output from external command, script, program, etc

@author lasers
"""

import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 60
    command = None
    format = '{output}'
    hide_warning = False
    max_width = -1
    msg_separator = '...'
    msg_warning = 'external: too many newlines'
    strip_whitespace = False
    symmetric = False

    def external(self):

        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        if self.command:
            output = subprocess.check_output(self.command,
                                             shell=True,
                                             universal_newlines=True)
            if len(output.split('\n')) > 2:
                output = output.split('\n')[0]
                self.hide_warning = True
            elif output[-1] == '\n':
                output = output.rstrip('\n')
                self.hide_warning = False

            if self.strip_whitespace:
                output = output.strip()

            if len(output) >= self.max_width:
                output = output[:self.max_width]

            if self.symmetric:
                split = int(self.max_width / 2) - 1
                output = output[:split] + self.msg_separator + output[-split:]

            if self.hide_warning:
                response['color'] = self.py3.COLOR_BAD
                output = self.msg_warning

            response['full_text'] = self.py3.safe_format(self.format, {'output': output})
        else:
            response['full_text'] = ''

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
