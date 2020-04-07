"""
Display SELinux state.

This module displays the state of SELinux on your machine:
Enforcing (good), Permissive (degraded), or Disabled (bad).

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'SELinux: {state}')
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
{'full_text': 'SELinux: enforcing', 'color': '#00FF00'}

permissive
{'full_text': 'SELinux: permissive', 'color': '#FFFF00'}

disabled
{'full_text': 'SELinux: disabled', 'color': '#FF0000'}
"""

import selinux


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "SELinux: {state}"
    state_disabled = "disabled"
    state_enforcing = "enforcing"
    state_permissive = "permissive"

    def selinux(self):
        try:
            if selinux.security_getenforce():
                state = self.state_enforcing
                color = self.py3.COLOR_GOOD
            else:
                state = self.state_permissive
                color = self.py3.COLOR_DEGRADED
        except AttributeError:
            state = self.state_disabled
            color = self.py3.COLOR_BAD

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"state": state}),
            "color": color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
