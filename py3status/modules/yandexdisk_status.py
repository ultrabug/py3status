# -*- coding: utf-8 -*-
"""
Display Yandex.Disk status.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'Yandex.Disk: {status}')
    status_busy: show when Yandex.Disk is busy (default None)
    status_off: show when Yandex.Disk isn't running (default 'Not started')
    status_on: show when Yandex.Disk is idling (default 'Idle')

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

SAMPLE OUTPUT
{'color': '#FFFF00', 'full_text': 'Yandex.Disk: Busy'}

idle
{'color': '#00FF00', 'full_text': 'Yandex.Disk: Idle'}

off
{'color': '#FF0000', 'full_text': 'Yandex.Disk: Not started'}
"""

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "Yandex.Disk: {status}"
    status_busy = None
    status_off = "Not started"
    status_on = "Idle"

    def post_config_hook(self):
        if not self.py3.check_commands("yandex-disk"):
            raise Exception(STRING_NOT_INSTALLED)

    def yandexdisk_status(self):
        status = self.py3.command_output("yandex-disk status").splitlines()[0]

        if status == "Error: daemon not started":
            color = self.py3.COLOR_BAD
            status = self.status_off
        elif status == "Synchronization core status: idle":
            color = self.py3.COLOR_GOOD
            status = self.status_on
        else:
            color = self.py3.COLOR_DEGRADED
            if self.status_busy is not None:
                status = self.status_busy

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "color": color,
            "full_text": self.py3.safe_format(self.format, {"status": status}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
