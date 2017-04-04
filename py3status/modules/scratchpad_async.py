# -*- coding: utf-8 -*-
"""
Display number of windows and urgency hints asynchronously.

Configuration parameters:
    format: display format for this module (default '[\?not_zero {counter} ⌫]')

Format placeholders:
    {counter} number of scratchpad windows

Requires:
    i3ipc: (https://github.com/acrisci/i3ipc-python)

@author cornerman
@license BSD

SAMPLE OUTPUT
{'full_text': '1 ⌫'}
"""

from threading import Thread

import i3ipc


class Py3status:
    """
    """
    # available configuration parameters
    format = u'[\?not_zero {counter} ⌫]'

    class Meta:
        deprecated = {
            'format_fix_unnamed_param': [
                {
                    'param': 'format',
                    'placeholder': 'counter',
                    'msg': '{} should not be used in format use `{counter}`',
                },
            ],
            'substitute_by_value': [
                {
                    'param': 'always_show',
                    'value': True,
                    'substitute': {
                        'param': 'format',
                        'value': '{counter} ⌫',
                    },
                    'msg': 'obsolete parameter, use new format',
                },
            ],
        }

    def post_config_hook(self):
        self.count = 0
        self.urgent = False

        t = Thread(target=self._listen)
        t.daemon = True
        t.start()

    def scratchpad_async(self):
        response = {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(
                self.format, {'counter': self.count}),
        }
        if self.urgent:
            response['urgent'] = True
        return response

    def _listen(self):
        def update_scratchpad_async(conn, e=None):
            cons = conn.get_tree().scratchpad().leaves()
            self.urgent = any(con for con in cons if con.urgent)
            self.count = len(cons)
            self.py3.update()

        conn = i3ipc.Connection()

        update_scratchpad_async(conn)

        conn.on('window::move', update_scratchpad_async)
        conn.on('window::urgent', update_scratchpad_async)

        conn.main()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        'format': '{counter} ⌫'
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
