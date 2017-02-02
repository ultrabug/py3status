# -*- coding: utf-8 -*-
"""
Display Yandex.Disk status.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'Yandex.Disk: {status}')
    string_busy: show when Yandex.Disk is busy (default 'Busy')
    string_off: show when Yandex.Disk isn't running (default 'Not started')
    string_on: show when Yandex.Disk is idling (default 'Idle')

Format placeholders:
    {status} Yandex.Disk status

Color options:
    color_bad: Not started
    color_degraded: Idle
    color_good: Busy

Requires:
    yandex-disk: command line interface for Yandex.Disk

@author Vladimir Potapev (github:vpotapev)
@license BSD
"""

string_error = "Yandex.Disk: isn't configured"
string_unavailable = "Yandex.Disk: isn't installed"


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'Yandex.Disk: {status}'
    string_busy = 'Busy'
    string_off = 'Not started'
    string_on = 'Idle'

    def yandex(self):
        if not self.py3.check_commands(["yandex-disk"]):
            return {'cached_until': self.py3.CACHE_FOREVER,
                    'color': self.py3.COLOR_BAD,
                    'full_text': string_unavailable}
        try:
            status = self.py3.command_output('yandex-disk status').splitlines()[0]
        except:
            return {'cache_until': self.py3.CACHE_FOREVER,
                    'color': self.py3.COLOR_ERROR or self.py3.COLOR_BAD,
                    'full_text': string_error}

        if status == "Error: daemon not started":
            color = self.py3.COLOR_BAD
            status = self.string_off
        elif status == "Synchronization core status: idle":
            color = self.py3.COLOR_GOOD
            status = self.string_on
        else:
            color = self.py3.COLOR_DEGRADED
            status = self.string_busy

        return {'cached_until': self.py3.time_in(self.cache_timeout),
                'color': color,
                'full_text': self.py3.safe_format(self.format, {'status': status})}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
