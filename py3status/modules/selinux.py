# -*- coding: utf-8 -*-
"""
Display SELinux state.

This module displays the state of SELinux on your machine:
Enforcing (good), Permissive (bad), or Disabled (bad).

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'selinux: {state}')
    state_disabled: show when no SELinux policy is loaded.
        (default 'disabled')
    state_enforcing: show when SELinux security policy is enforced.
        (default 'enforcing')
    state_permissive: show when SELinux prints warnings instead of enforcing.
        (default 'permissive')

Format placeholders:
    {state} SELinux state

Color options:
    color_bad: Enforcing
    color_degraded: Permissive
    color_good: Disabled

Requires:
    libselinux-python: SELinux python bindings for libselinux

@author bstinsonmhk
@license BSD

SAMPLE OUTPUT
{'full_text': 'selinux: enforcing', 'color': '#00FF00'}

permissive
{'full_text': 'selinux: permissive', 'color': '#FFFF00'}

disabled
{'full_text': 'selinux: disabled', 'color': '#FF0000'}
"""
from __future__ import absolute_import
import selinux
STRING_UNAVAILABLE = "selinux: isn't installed"


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = 'selinux: {state}'
    state_disabled = 'disabled'
    state_enforcing = 'enforcing'
    state_permissive = 'permissive'

    def selinux(self):
        if not self.py3.check_commands(['getenforce']):
            return {'cache_until': self.py3.CACHE_FOREVER,
                    'color': self.py3.COLOR_BAD,
                    'full_text': STRING_UNAVAILABLE}
        try:
            if selinux.security_getenforce():
                state = self.state_enforcing
                color = self.py3.COLOR_GOOD
            else:
                state = self.state_permissive
                color = self.py3.COLOR_BAD
        except:
            state = self.state_disabled
            color = self.py3.COLOR_BAD

        return {'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format, {'state': state}),
                'color': color}


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
