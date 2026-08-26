"""
Native reimplementation of i3status's `time` module.

Outputs the current time in the local timezone. See strftime(3) for
format directives; unlike most other placeholders in this package, the
format string here is a raw strftime pattern, not %name placeholders.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: strftime(3) format string (default '%Y-%m-%d %H:%M:%S')

Type: Singleton (supports only one, unnamed section)

@author claude
"""

from datetime import datetime

from py3status.i3status.helpers import resolve_cache_timeout


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%Y-%m-%d %H:%M:%S"

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)

    def time(self):
        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": datetime.now().strftime(self.format),
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
