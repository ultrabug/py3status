"""
Native reimplementation of i3status's `ddate` module.

Outputs the current discordian date in user-specified format. See
ddate(1) for details on the format string.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: see placeholders below (default '%{%a, %b %d%}, %Y%N - %H')

Format placeholders:
    %A weekday, long (eg Sweetmorn)
    %a weekday, short (eg SM)
    %B season, long (eg Discord)
    %b season, short (eg Dsc)
    %d day of the season, cardinal (eg 5)
    %e day of the season, ordinal (eg 5th)
    %Y year of our lady of discord (YOLD)
    %H holiday name, only non-empty on the 5th or 50th day of a season
    %N empty, unless on a holiday
    %n a newline
    %t a tab
    %{...%} content shown only when it is NOT St. Tib's Day; on St. Tib's
        Day itself the whole %{...%} span is replaced by "St. Tib's Day"

Type: Singleton (supports only one, unnamed section)

Notes:
    Deviates from the real i3status 2.15 binary, which reads several
    uninitialized C buffers here: %H prints garbage bytes on ~97% of
    days (confirmed by inspection) and %{...%} unconditionally prepends
    "St. Tib's Day" regardless of the actual day. This implementation
    does what the man page and classic ddate(1) actually document
    instead, and also fixes a double ordinal-suffix bug (the C code
    appends "th" then a second, conflicting suffix for days 11-13, eg
    "11thst").

    The year-2000-leap-year quirk in the C source (computing leap years
    from tm_year, ie years since 1900, whose %100/%400 checks drift
    from the real calendar year) IS preserved here, since it's a
    deterministic algorithmic property of the original tool, not a
    memory bug - it only differs on century years.

@author claude
"""

import re
from datetime import date

from py3status.i3status.helpers import resolve_cache_timeout

SEASON_LONG = ["Chaos", "Discord", "Confusion", "Bureaucracy", "The Aftermath"]
SEASON_SHORT = ["Chs", "Dsc", "Cfn", "Bcy", "Afm"]
DAY_LONG = ["Sweetmorn", "Boomtime", "Pungenday", "Prickle-Prickle", "Setting Orange"]
DAY_SHORT = ["SM", "BT", "PD", "PP", "SO"]
HOLIDAYS = [
    "Mungday",
    "Mojoday",
    "Syaday",
    "Zaraday",
    "Maladay",
    "Chaoflux",
    "Discoflux",
    "Confuflux",
    "Bureflux",
    "Afflux",
]

TIBS_BLOCK_RE = re.compile(r"%\{(.*?)%\}", re.DOTALL)


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%{%a, %b %d%}, %Y%N - %H"

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)

    @staticmethod
    def _ordinal_suffix(day):
        if 11 <= day % 100 <= 13:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    @staticmethod
    def _discordian_date(today):
        tm_year = today.year - 1900
        # matches the original tool's leap-year check against tm_year, not the
        # real calendar year - see the module docstring
        is_leap_year = not (tm_year % 4) and (not (tm_year % 400) or bool(tm_year % 100))

        yday = today.timetuple().tm_yday - 1  # 0-indexed, to match C's tm_yday

        st_tibs_day = is_leap_year and yday == 59
        if st_tibs_day:
            season_day = week_day = season = None
        else:
            if is_leap_year and yday > 59:
                yday -= 1
            season_day = yday % 73
            week_day = yday % 5
            season = yday // 73

        year = today.year + 1166
        holiday = None
        if not st_tibs_day:
            if season_day == 4:
                holiday = HOLIDAYS[season]
            elif season_day == 49:
                holiday = HOLIDAYS[season + 5]

        return {
            "st_tibs_day": st_tibs_day,
            "season": season,
            "week_day": week_day,
            "season_day": season_day,
            "year": year,
            "holiday": holiday,
        }

    def _render(self, dt):
        day = None if dt["season_day"] is None else dt["season_day"] + 1
        return {
            "%A": "" if dt["week_day"] is None else DAY_LONG[dt["week_day"]],
            "%a": "" if dt["week_day"] is None else DAY_SHORT[dt["week_day"]],
            "%B": "" if dt["season"] is None else SEASON_LONG[dt["season"]],
            "%b": "" if dt["season"] is None else SEASON_SHORT[dt["season"]],
            "%d": "" if day is None else str(day),
            "%e": "" if day is None else f"{day}{self._ordinal_suffix(day)}",
            "%Y": str(dt["year"]),
            "%H": dt["holiday"] or "",
            "%N": "",
            "%n": "\n",
            "%t": "\t",
        }

    def ddate(self):
        dt = self._discordian_date(date.today())

        def resolve_tibs_block(match):
            return "St. Tib's Day" if dt["st_tibs_day"] else match.group(1)

        format_string = TIBS_BLOCK_RE.sub(resolve_tibs_block, self.format)

        values = self._render(dt)
        for name, value in values.items():
            format_string = format_string.replace(name, value)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_string,
        }


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
