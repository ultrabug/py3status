# -*- coding: utf-8 -*-
"""
Display the amount of windows and indicate urgency hints on scratchpad (async).

Configuration parameters:
    always_show: whether the indicator should be shown if there are no
        scratchpad windows (default False)
    format: Display format when one or more scratchpad window(s) (default "{counter} ⌫")

Requires:
    i3ipc: (https://github.com/acrisci/i3ipc-python)

@author cornerman
@license BSD
"""

from threading import Thread
import i3ipc


class Py3status:
    """
    """
    # available configuration parameters
    always_show = False
    format = u'{counter} ⌫'

    def __init__(self):
        self.count = 0
        self.urgent = False

        t = Thread(target=self._listen)
        t.daemon = True
        t.start()

    def scratchpad_async(self):
        response = {'cached_until': self.py3.CACHE_FOREVER}

        if self.urgent:
            response['urgent'] = True

        if self.always_show or self.count > 0:
            response['full_text'] = self.py3.safe_format(self.format, {'counter': self.count})
        else:
            response['full_text'] = ''

        return response

    def _listen(self):
        def update_scratchpad_async(conn, e=None):
            cons = conn.get_tree().scratchpad().leaves()
            self.urgent = any(con for con in cons if con.urgent)
            self.count = len(cons)
            self.py3.update()

        conn = i3ipc.Connection()
        conn.on('window::move', update_scratchpad_async)
        conn.on('window::urgent', update_scratchpad_async)
        conn.main()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        'always_show': True
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
