# -*- coding: utf-8 -*-
"""
Display the amount of windows and indicate urgency hints on scratchpad (async).

Configuration parameters:
    always_show: whether the indicator should be shown if there are no
        scratchpad windows (default False)
    color_urgent: color to use if a scratchpad window is urgent (default
        "#900000")
    format: string to format the output (default "{} ⌫")

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
    color_urgent = "#900000"
    format = "{} ⌫"

    def __init__(self):
        self.count = 0
        self.urgent = False

        t = Thread(target=self._listen)
        t.daemon = True
        t.start()

    def scratchpad_counter(self, i3s_output_list, i3s_config):
        response = {'cached_until': self.py3.CACHE_FOREVER}

        if self.urgent:
            response['color'] = self.color_urgent

        if self.always_show or self.count > 0:
            response['full_text'] = self.format.format(self.count)
        else:
            response['full_text'] = ''

        return response

    def _listen(self):
        def update_scratchpad_counter(conn, e=None):
            cons = conn.get_tree().scratchpad().leaves()
            self.urgent = any(con for con in cons if con.urgent)
            self.count = len(cons)
            self.py3.update()

        conn = i3ipc.Connection()

        update_scratchpad_counter(conn)

        conn.on('window::move', update_scratchpad_counter)
        conn.on('window::urgent', update_scratchpad_counter)

        conn.main()


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.scratchpad_counter([], config))
        sleep(1)
