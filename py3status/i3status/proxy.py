r"""
Proxy i3status modules as real py3status modules.

# INTERNAL PROXY MODULE, NOT FOR DIRECT CONFIGURATION.
# See py3status/modules/i3status.py to configure modules.

Configuration parameters:
    cache_timeout: refresh interval for this module, otherwise the
        container's own general interval (default None)
    format_module: display format for this module (default '{output}')

format_module placeholders:
    {output} the i3status module's output

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'USED_DISK '},
    {'full_text': '42%', 'color': '#90EE90'}
]
"""

import time
from datetime import datetime, timezone

from py3status.i3status import registry
from py3status.i3status.constants import I3S_TIME_MODULES


class TimeZoneTicker:
    """
    Ticks time/tztime locally, independent of the container's own (much
    slower) poll rate.
    """

    # extra slack beyond one container poll cycle before treating an
    # overdue schedule as suspicious (suspend/resume), not just jitter
    OVERDUE_SLACK_SECONDS = 5

    def __init__(self, time_format, interval):
        self.time_format = time_format
        self.time_delta = self._time_delta_for(time_format)
        self._interval = interval
        self._tz = None
        self._check_due = 0

    @staticmethod
    def _time_delta_for(time_format):
        # how granular a time/tztime module's local tick needs to be
        if "%f" in time_format:
            return 0
        if any(code in time_format for code in ("%S", "%s", "%T", "%c", "%+", "%X")):
            return 1
        return 60

    def _set_time_zone(self, raw_full_text):
        parts = raw_full_text.encode("UTF-8", "replace").decode().split()
        if len(parts) < 3:
            # occasionally we do not get the timezone name
            return True

        try:
            date = datetime.strptime(" ".join(parts[:2]), I3S_TIME_MODULES["time"])
        except ValueError:
            return False

        utcnow = datetime.now(timezone.utc)
        delta = datetime(date.year, date.month, date.day, date.hour, date.minute) - datetime(
            utcnow.year, utcnow.month, utcnow.day, utcnow.hour, utcnow.minute
        )
        try:
            self._tz = timezone(delta, parts[2])
        except ValueError:
            return False
        return True

    def refresh(self, raw_full_text):
        # re-derive the timezone from i3status's own raw reading, if
        # due - call each time the container publishes a fresh one
        now = time.monotonic()
        if self._check_due >= now:
            return
        if not self._set_time_zone(raw_full_text):
            # unparseable, probably a suspend/resume glitch - retry on
            # the very next reading instead of waiting
            self._check_due = 0
        elif self._check_due and (
            now - self._check_due > self.OVERDUE_SLACK_SECONDS + self._interval
        ):
            # very overdue - the reading this was based on may be stale,
            # don't trust it for a further 30 minutes
            self._check_due = 0
        else:
            # recheck in 30 min regardless, in case DST just switched -
            # aligned to monotonic time, not the wall clock, so NTP/
            # manual clock changes can't skew the schedule
            self._check_due = ((int(now) // 1800) * 1800) + 1800

    def render(self):
        return datetime.now(self._tz).strftime(self.time_format)


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format_module = "{output}"

    def post_config_hook(self):
        self._container = getattr(self, "_container", None)
        item_name = getattr(self, "_item_name", None)
        if not self._container or not item_name:
            raise Exception("internal proxy module, not for direct configuration")
        self._key = (item_name, getattr(self, "_item_instance", None))
        # translate.py always resolves these - only missing if built directly
        if self.cache_timeout is None:
            self.cache_timeout = 1
        self._interval = getattr(self, "_interval", 1)
        # explicit cache_timeout - honor it over the format's tick rate
        self._cache_timeout = getattr(self, "_cache_timeout", False)
        # strip i3status's own per-block fields - block Composite.simplify() merges
        self.block_fields = ("name", "instance", "markup", "separator", "separator_block_width")
        # one condition drives both: which ticker object, and which renderer
        is_ticker = item_name in I3S_TIME_MODULES
        self._ticker = TimeZoneTicker(self.format, self._interval) if is_ticker else None
        self._render_response = self._time_proxy if is_ticker else self._registry_proxy

    def _time_proxy(self):
        item = registry.read(self._container, self._key)
        if item is not None:
            self._ticker.refresh(item.get("full_text", ""))

        output = {"output": self._ticker.render()}
        composite = self.py3.safe_format(self.format_module, output, force_composite=True)
        if self._cache_timeout:
            cached_until = self.py3.time_in(self.cache_timeout)
        else:
            cached_until = self.py3.time_in(sync_to=self._ticker.time_delta)

        return {"cached_until": cached_until, "composite": composite}

    def _registry_proxy(self):
        # every non-ticker item: just relay the container's last reading
        item = registry.read(self._container, self._key)
        if item is None:
            cached_until = self.py3.time_in(self.cache_timeout)
            return {"cached_until": cached_until, "full_text": ""}

        item = dict(item)
        for key in self.block_fields:
            item.pop(key, None)

        output = {"output": self.py3.composite_create(item)}
        composite = self.py3.safe_format(self.format_module, output, force_composite=True)
        cached_until = self.py3.time_in(self.cache_timeout)

        return {"cached_until": cached_until, "composite": composite}

    def i3status_proxy(self):
        dead_reason = registry.dead_reason(self._container)
        if dead_reason:
            # container is dead for good - a visible, clickable error
            # is better than silently rendering nothing forever
            self.py3.error(dead_reason, self.py3.CACHE_FOREVER)

        return self._render_response()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    registry.publish(
        "i3status _generated",
        ("disk", "/"),
        {"name": "disk", "instance": "/", "full_text": "42%"},
    )
    config = {
        "_container": "i3status _generated",
        "_item_name": "disk",
        "_item_instance": "/",
        "format_module": r"USED_DISK [\?color=lightgreen {output}]",
    }
    module_test(Py3status, config=config)
