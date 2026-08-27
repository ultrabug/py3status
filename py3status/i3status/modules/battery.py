"""
Native reimplementation of i3status's `battery` module.

Gets the status (charging, discharging, unknown, full), percentage,
remaining time and power consumption (in Watts) of the given battery
and when it's estimated to be empty.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    format: see placeholders below (default '%status %percentage %remaining')
    format_down: format used when no battery information is available
        (default 'No battery')
    format_percentage: printf-style format for %percentage (default '%.02f%s')
    hide_seconds: hide seconds in %remaining/%emptytime (default True)
    last_full_capacity: use the battery's last full charge instead of its
        design capacity as 100%, and clamp %percentage to 100
        (default False)
    low_threshold: threshold, interpreted per threshold_type, below which
        color_bad is used while discharging (default 30)
    number: battery number (eg 0 for BAT0), or 'all' (case-insensitive)
        to aggregate every battery matching path's '%d' wildcard
        (default 0)
    path: path to a battery's uevent file, with '%d' as the battery
        number (default '/sys/class/power_supply/BAT%d/uevent')
    status_bat: %status text while discharging (default 'BAT')
    status_chr: %status text while charging (default 'CHR')
    status_full: %status text when full (default 'FULL')
    status_idle: %status text when not charging (default 'IDLE')
    status_unk: %status text when unknown (default 'UNK')
    threshold_type: 'time' or 'percentage', what low_threshold is
        interpreted as (default 'time')

Format placeholders:
    %status one of status_chr/status_bat/status_full/status_idle/status_unk
    %percentage remaining charge, formatted per format_percentage
    %remaining time remaining until empty/full, as [HH:]MM:SS
    %emptytime wall-clock time when the battery will be empty/full
    %consumption current power draw in Watts, eg '12.34W'

Color options:
    color_bad: discharging and low_threshold (per threshold_type)
        applies

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Real i3status has no 'number' config key - it comes from the
    section's title instead (eg `battery 0 { }` gives number=0,
    `battery all { }` aggregates every battery). This module exposes
    'number' as an ordinary config key instead, so it works with zero
    config; it's stripped automatically if the section resolves to the
    real i3status wrapper, since real i3status crashes on an
    unrecognized option.

    Output is trimmed of leading/trailing whitespace, matching
    i3status.

    'integer_battery_capacity' is a real, deprecated-upstream i3status
    option (cfg_opt_t battery_opts) - supported for anyone migrating an
    existing i3status.conf, but deliberately left out of
    'Configuration parameters' above and off the class body so it
    isn't advertised. Matches real i3status's own legacy semantics: it
    only takes effect if format_percentage is still the literal default
    '%.02f%s' (overridden to '%.00f%s'); otherwise it's a no-op and a
    deprecation warning is logged instead.

@author claude
"""

from glob import glob
from time import localtime, time

from py3status.i3status.helpers import format_placeholders, resolve_cache_timeout

STATUS_CHARGING = "charging"
STATUS_DISCHARGING = "discharging"
STATUS_FULL = "full"
STATUS_IDLE = "idle"
STATUS_UNKNOWN = "unknown"

UEVENT_FIELDS = {
    "POWER_SUPPLY_ENERGY_NOW": "energy_now",
    "POWER_SUPPLY_CHARGE_NOW": "charge_now",
    "POWER_SUPPLY_CAPACITY": "capacity",
    "POWER_SUPPLY_CURRENT_NOW": "current_now",
    "POWER_SUPPLY_POWER_NOW": "power_now",
    "POWER_SUPPLY_VOLTAGE_NOW": "voltage_now",
    "POWER_SUPPLY_TIME_TO_EMPTY_NOW": "time_to_empty_now",
    "POWER_SUPPLY_STATUS": "status",
    "POWER_SUPPLY_CHARGE_FULL_DESIGN": "charge_full_design",
    "POWER_SUPPLY_ENERGY_FULL_DESIGN": "energy_full_design",
    "POWER_SUPPLY_ENERGY_FULL": "energy_full",
    "POWER_SUPPLY_CHARGE_FULL": "charge_full",
}


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    format = "%status %percentage %remaining"
    format_down = "No battery"
    format_percentage = "%.02f%s"
    hide_seconds = True
    last_full_capacity = False
    low_threshold = 30
    number = 0
    path = "/sys/class/power_supply/BAT%d/uevent"
    status_bat = "BAT"
    status_chr = "CHR"
    status_full = "FULL"
    status_idle = "IDLE"
    status_unk = "UNK"
    threshold_type = "time"

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)
        # undocumented, real i3status option (see Notes above) - support it
        # if a user (or a test) sets it, without advertising it as a
        # supported config key
        if getattr(self, "integer_battery_capacity", False):
            if self.format_percentage == "%.02f%s":
                self.format_percentage = "%.00f%s"
            else:
                self.py3.log(
                    "battery: integer_battery_capacity is deprecated",
                    level=self.py3.LOG_WARNING,
                )
        self._number_is_all = str(self.number).lower() == "all"
        if self._number_is_all:
            self._glob_pattern = self.path.replace("%d", "*")
        else:
            self._number = int(self.number)
        self._threshold_type_lower = self.threshold_type.lower()
        self._status_text = {
            STATUS_CHARGING: self.status_chr,
            STATUS_DISCHARGING: self.status_bat,
            STATUS_FULL: self.status_full,
            STATUS_IDLE: self.status_idle,
        }

    @staticmethod
    def _read_uevent(path):
        fields = {}
        with open(path) as f:
            for line in f:
                line = line.strip()
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key in UEVENT_FIELDS:
                    fields[UEVENT_FIELDS[key]] = value
        return fields

    def _parse_battery(self, path):
        """Return a dict describing one battery, or None if path is unreadable."""
        try:
            fields = self._read_uevent(path)
        except OSError:
            return None

        remaining = -1
        percentage = -1
        watt_as_unit = False
        if "energy_now" in fields:
            watt_as_unit = True
            remaining = int(fields["energy_now"])
        elif "charge_now" in fields:
            remaining = int(fields["charge_now"])
        if remaining == -1 and "capacity" in fields:
            percentage = int(fields["capacity"])

        present_rate = 0
        if "current_now" in fields:
            present_rate = abs(int(fields["current_now"]))
        elif "power_now" in fields:
            present_rate = abs(int(fields["power_now"]))

        voltage = int(fields["voltage_now"]) if "voltage_now" in fields else -1

        seconds_remaining = -1
        if "time_to_empty_now" in fields:
            seconds_remaining = abs(int(fields["time_to_empty_now"])) * 60

        status_field = fields.get("status", "")
        if status_field == "Charging":
            status = STATUS_CHARGING
        elif status_field == "Full":
            status = STATUS_FULL
        elif status_field == "Discharging":
            status = STATUS_DISCHARGING
        elif status_field == "Not charging":
            status = STATUS_IDLE
        elif status_field:
            status = STATUS_UNKNOWN
        else:
            status = STATUS_UNKNOWN

        full_design = int(fields.get("charge_full_design", fields.get("energy_full_design", -1)))
        full_last = int(fields.get("energy_full", fields.get("charge_full", -1)))

        if not watt_as_unit and voltage >= 0:
            if present_rate > 0:
                present_rate = (voltage / 1000.0) * (present_rate / 1000.0)
            if remaining > 0:
                remaining = (voltage / 1000.0) * (remaining / 1000.0)
            if full_design > 0:
                full_design = (voltage / 1000.0) * (full_design / 1000.0)
            if full_last > 0:
                full_last = (voltage / 1000.0) * (full_last / 1000.0)

        return {
            "full_design": full_design,
            "full_last": full_last,
            "remaining": remaining,
            "present_rate": present_rate,
            "seconds_remaining": seconds_remaining,
            "percentage_remaining": percentage,
            "status": status,
        }

    @staticmethod
    def _merge_status(acc_status, batt_status, present_rate):
        if acc_status == STATUS_UNKNOWN:
            return batt_status
        if acc_status == STATUS_DISCHARGING:
            return STATUS_CHARGING if present_rate > 0 else acc_status
        if acc_status == STATUS_CHARGING:
            return STATUS_DISCHARGING if present_rate < 0 else acc_status
        if acc_status == STATUS_FULL:
            return batt_status if batt_status != STATUS_UNKNOWN else acc_status
        if acc_status == STATUS_IDLE:
            if batt_status not in (STATUS_UNKNOWN, STATUS_FULL):
                return batt_status
            return acc_status
        return acc_status

    def _aggregate(self, batteries):
        acc = {
            "full_design": 0,
            "full_last": 0,
            "remaining": 0,
            "present_rate": 0,
            "seconds_remaining": -1,
            "percentage_remaining": -1,
            "status": STATUS_UNKNOWN,
        }
        signed_rate = 0
        for batt in batteries:
            acc["full_design"] += max(batt["full_design"], 0)
            acc["full_last"] += max(batt["full_last"], 0)
            acc["remaining"] += max(batt["remaining"], 0)

            this_signed = (-1 if acc["status"] == STATUS_DISCHARGING else 1) * signed_rate
            this_signed += (-1 if batt["status"] == STATUS_DISCHARGING else 1) * batt[
                "present_rate"
            ]
            acc["status"] = self._merge_status(acc["status"], batt["status"], this_signed)
            signed_rate = this_signed

        acc["present_rate"] = abs(signed_rate)
        return acc

    def _down(self):
        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.format_down,
        }

    def battery(self):
        if self._number_is_all:
            batteries = [self._parse_battery(p) for p in sorted(glob(self._glob_pattern))]
            batteries = [b for b in batteries if b is not None]
            if not batteries:
                return self._down()
            batt = self._aggregate(batteries)
        else:
            batt = self._parse_battery(self.path % self._number)
            if batt is None:
                return self._down()

        full = batt["full_design"]
        if full <= 0 or (self.last_full_capacity and batt["full_last"] > 0):
            full = batt["full_last"]
        if full <= 0 and batt["remaining"] < 0 and batt["percentage_remaining"] < 0:
            return self._down()

        percentage = batt["percentage_remaining"]
        if percentage < 0:
            percentage = (batt["remaining"] / full) * 100
            if self.last_full_capacity and percentage > 100:
                percentage = 100

        seconds_remaining = batt["seconds_remaining"]
        if seconds_remaining < 0 and batt["present_rate"] > 0 and batt["status"] != STATUS_FULL:
            if batt["status"] == STATUS_CHARGING:
                seconds_remaining = 3600.0 * (full - batt["remaining"]) / batt["present_rate"]
            elif batt["status"] == STATUS_DISCHARGING:
                seconds_remaining = 3600.0 * batt["remaining"] / batt["present_rate"]
            else:
                seconds_remaining = 0

        color = None
        if batt["status"] == STATUS_DISCHARGING and self.low_threshold > 0:
            if (
                percentage >= 0
                and self._threshold_type_lower == "percentage"
                and percentage < self.low_threshold
            ):
                color = self.py3.COLOR_BAD
            elif (
                seconds_remaining >= 0
                and self._threshold_type_lower == "time"
                and seconds_remaining < 60 * self.low_threshold
            ):
                color = self.py3.COLOR_BAD

        status_text = self._status_text.get(batt["status"], self.status_unk)

        remaining_str = ""
        emptytime_str = ""
        if seconds_remaining >= 0:
            hours, rem = divmod(int(seconds_remaining), 3600)
            minutes, seconds = divmod(rem, 60)
            if self.hide_seconds:
                remaining_str = f"{max(hours, 0):02d}:{max(minutes, 0):02d}"
            else:
                remaining_str = f"{max(hours, 0):02d}:{max(minutes, 0):02d}:{max(seconds, 0):02d}"

            empty_tm = localtime(time() + seconds_remaining)
            if self.hide_seconds:
                emptytime_str = f"{empty_tm.tm_hour:02d}:{empty_tm.tm_min:02d}"
            else:
                emptytime_str = (
                    f"{empty_tm.tm_hour:02d}:{empty_tm.tm_min:02d}:{empty_tm.tm_sec:02d}"
                )

        consumption_str = ""
        if batt["present_rate"] >= 0:
            consumption_str = f"{batt['present_rate'] / 1e6:1.2f}W"

        placeholders = [
            ("%status", status_text),
            ("%percentage", self.format_percentage % (percentage, "%")),
            ("%remaining", remaining_str),
            ("%emptytime", emptytime_str),
            ("%consumption", consumption_str),
        ]

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(self.format, placeholders).strip(),
        }
        if color:
            response["color"] = color
        return response


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
