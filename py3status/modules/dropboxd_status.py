# -*- coding: utf-8 -*-
"""
Display status of Dropbox daemon.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'Dropbox: {status}')
    string_busy: show when Dropbox is busy (default None)
    string_off: show when Dropbox isn't running (default None)
    string_on: show when Dropbox is up to date (default None)
    string_unavailable: show when Dropbox isn't installed (default "Dropbox isn't installed!")

Valid status values include:
    - Dropbox isn't running!
    - Starting...
    - Downloading file list...
    - Syncing "filename"
    - Up to date

Format placeholders:
    {status} current Dropbox status

Color options:
    color_bad: Not running
    color_degraded: Busy
    color_good: Up to date

Requires:
    dropbox-cli: command line interface for dropbox

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD
"""


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'Dropbox: {status}'
    string_busy = None
    string_off = None
    string_on = None
    string_unavailable = "Dropbox isn't installed!"

    class Meta:
        deprecated = {
            'format_fix_unnamed_param': [
                {
                    'param': 'format',
                    'placeholder': 'status',
                    'msg': '{} should not be used in format use `{status}`',
                },
            ],
        }

    def dropbox(self):
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        try:
            status = self.py3.command_output('dropbox-cli status').splitlines()[0]
        except:
            response['cached_until'] = self.py3.CACHE_FOREVER
            response['color'] = self.py3.COLOR_BAD
            response['full_text'] = self.string_unavailable
        else:
            if status == "Dropbox isn't running!":
                status = status.replace('Dropbox ', '')
                response['color'] = self.py3.COLOR_BAD
                if self.string_off != '':
                    status = self.string_off

            elif status == "Up to date":
                response['color'] = self.py3.COLOR_GOOD
                if self.string_on != '':
                    status = self.string_on
            else:
                response['color'] = self.py3.COLOR_DEGRADED
                if self.string_busy != '':
                    status = self.string_busy

            response['full_text'] = self.py3.safe_format(
                self.format, {'status': status})

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
