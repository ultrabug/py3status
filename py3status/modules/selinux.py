# -*- coding: utf-8 -*-
"""
Display SELinux state.

This module displays the current state of selinux on your machine: Enforcing
(good), Permissive (bad), or Disabled (bad).

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 10)
    format: see placeholders below, (default 'selinux: {state}')

Format placeholders:
    {state} the current selinux state

Color options:
    color_bad: Enforcing
    color_degraded: Permissive
    color_good: Disabled

Requires:
    libselinux-python:
        or
    libselinux-python3: (optional for python3 support)

@author bstinsonmhk
@license BSD
"""

from __future__ import absolute_import
import selinux


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'selinux: {state}'

    def selinux_status(self):
        try:
            if selinux.security_getenforce():
                selinuxstring = 'enforcing'
                color = self.py3.COLOR_GOOD
            else:
                selinuxstring = 'permissive'
                color = self.py3.COLOR_BAD
        except OSError:
            selinuxstring = 'disabled'
            color = self.py3.COLOR_BAD

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'state': selinuxstring}),
            'color': color,
        }

        return response


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
