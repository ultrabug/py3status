# -*- coding: utf-8 -*-
"""
Display SELinux state.

This module displays the current state of selinux on your machine:
Enforcing (good), Permissive (bad), or Disabled (bad).

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'selinux: {state}')
    string_disabled: show when no SELinux policy is loaded.
        (default 'disabled')
    string_enforcing: show when SELinux security policy is enforced.
        (default 'enforcing')
    string_permissive: show when SELinux prints warnings instead of enforcing.
        (default 'permissive')

Format placeholders:
    {state} current selinux state

Color options:
    color_bad: Enforcing
    color_degraded: Permissive
    color_good: Disabled

Requires:
    libselinux-python: SELinux python bindings for libselinux

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
    string_disabled = 'disabled'
    string_enforcing = 'enforcing'
    string_permissive = 'permissive'

    def selinux_status(self):
        try:
            if selinux.security_getenforce():
                state = self.string_enforcing
                color = self.py3.COLOR_GOOD
            else:
                state = self.string_permissive
                color = self.py3.COLOR_BAD
        except:
            state = self.string_disabled
            color = self.py3.COLOR_BAD

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'state': state}),
            'color': color
        }


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
