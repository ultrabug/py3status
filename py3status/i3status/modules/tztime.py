"""
Native reimplementation of i3status's `tztime` module.

Outputs the current time in the given timezone. See strftime(3) for
format directives; unlike most other placeholders in this package, the
format string here is a raw strftime pattern, not %name placeholders -
except %time, see format_time below.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: strftime(3) format string, or a literal string containing
        %time if format_time is set (default '%Y-%m-%d %H:%M:%S %Z')
    format_time: if set, this strftime(3) pattern is rendered and
        substituted for %time in format - useful to add markup around
        the time without it being escaped by strftime (default None)
    hide_if_equals_localtime: hide the module (empty output) when
        timezone currently has the same UTC offset as local time
        (default False)
    locale: locale to use for this module's strftime output, eg
        'de_DE.UTF-8'; empty uses the environment's locale (default '')
    timezone: an IANA timezone name, eg 'Europe/Berlin'; empty uses
        local time (default '')

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Real i3status has a bug here: it scans format_time itself for
    %time instead of scanning format. Since format_time is normally a
    raw strftime pattern (not containing "%time" literally), the
    documented "add markup around the time" use case is non-functional
    there in practice. This module implements the intended behavior
    instead: format_time's rendered value substitutes into format's
    %time placeholder.

    locale.setlocale() is process-global, not thread-local, and
    py3status runs each module on its own thread - concurrent tztime
    instances with different locale settings could transiently observe
    each other's locale mid-format. A module-level lock serializes
    locale-touching calls across all tztime instances to prevent that
    (it can't protect against unrelated locale-sensitive code elsewhere
    in the process). Real i3status doesn't have this problem since
    it's single-threaded.

@author claude
"""

import threading
from datetime import datetime
from locale import LC_ALL, setlocale
from zoneinfo import ZoneInfo

from py3status.i3status.helpers import resolve_cache_timeout

_locale_lock = threading.Lock()


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%Y-%m-%d %H:%M:%S %Z"
    format_time = None
    hide_if_equals_localtime = False
    locale = ""
    timezone = ""

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        self._tz = ZoneInfo(self.timezone) if self.timezone else None

    def _strftime(self, fmt, when):
        if not self.locale:
            return when.strftime(fmt)
        with _locale_lock:
            prev = setlocale(LC_ALL)
            try:
                setlocale(LC_ALL, self.locale)
                return when.strftime(fmt)
            finally:
                setlocale(LC_ALL, prev)

    def tztime(self):
        now = datetime.now().astimezone()
        target = now.astimezone(self._tz) if self._tz else now

        if self.hide_if_equals_localtime and target.utcoffset() == now.utcoffset():
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": "",
            }

        if self.format_time is not None:
            time_str = self._strftime(self.format_time, target)
            full_text = self.format.replace("%time", time_str)
        else:
            full_text = self._strftime(self.format, target)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
