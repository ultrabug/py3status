r"""
Display disk information.

Configuration parameters:
    cache_timeout: refresh interval for this module. (default 10)
    disk: show stats for disk or partition, i.e. `sda1`. None for all disks.
        (default None)
    format: display format for this module.
        (default "{disk}: {used_percent}% ({total})")
    format_rate: display format for rates value
        (default "[\?min_length=11 {value:.1f} {unit}]")
    format_space: display format for disk space values
        (default "[\?min_length=5 {value:.1f}]")
    sector_size: size of the disk's sectors.
        (default 512)
    si_units: use SI units
        (default False)
    thresholds: specify color thresholds to use
        *(default {'free': [(0, 'bad'), (10, 'degraded'), (100, 'good')],
        'total': [(0, 'good'), (1024, 'degraded'), (1024 * 1024, 'bad')],
        'used_percent': [(0, 'good'), (40, 'degraded'), (75, 'bad')]})*
    unit: unit to use. If the unit contains a multiplier prefix, only this
        exact unit will ever be used
        (default "B/s")

Format placeholders:
    {disk} the selected disk
    {free} free space on disk in GB
    {used} used space on disk in GB
    {total_space} total space on disk in GB
    {used_percent} used space on disk in %
    {read} reading rate
    {total} total IO rate
    {write} writing rate

format_rate placeholders:
    {unit} name of the unit
    {value} numeric value of the rate

format_space placeholders:
    {value} numeric value of the free/used space on the device

Color thresholds:
    {free} Change color based on the value of free
    {used} Change color based on the value of used
    {used_percent} Change color based on the value of used_percent
    {read} Change color based on the value of read
    {total} Change color based on the value of total
    {write} Change color based on the value of write

@author guiniol
@license BSD

SAMPLE OUTPUT
{'full_text': 'all:  34.4% ( 82.0 KiB/s)'}
"""

import time
from pathlib import Path


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    disk = None
    format = "{disk}: {used_percent}% ({total})"
    format_rate = r"[\?min_length=11 {value:.1f} {unit}]"
    format_space = r"[\?min_length=5 {value:.1f}]"
    sector_size = 512
    si_units = False
    thresholds = {
        "free": [(0, "bad"), (10, "degraded"), (100, "good")],
        "total": [(0, "good"), (1024, "degraded"), (1024 * 1024, "bad")],
        "used_percent": [(0, "good"), (40, "degraded"), (75, "bad")],
    }
    unit = "B/s"

    def post_config_hook(self):
        self.disk_name = self.disk or "all"
        names_and_matches = [
            ("df", ["free", "used", "used_percent", "total_space"]),
            ("diskstats", ["read", "write", "total"]),
        ]
        self.init = {x[0]: {} for x in names_and_matches}
        for name, match in names_and_matches:
            placeholders = self.py3.get_placeholders_list(self.format, match)
            if placeholders:
                self.init[name] = {"placeholders": placeholders, "keys": match}

        if self.init["diskstats"]:
            self.last_diskstats = self._get_diskstats(self.disk)
            self.last_time = time.perf_counter()

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def _get_df_usages(self, disk):
        try:
            df_usages = self.py3.command_output(["df", "-k"])
        except self.py3.CommandError as ce:
            df_usages = ce.output
        total, used, free, devs = 0, 0, 0, []

        if disk and not disk.startswith("/dev/"):
            disk = "/dev/" + disk

        for line in df_usages.splitlines():
            if (disk and line.startswith(disk)) or (
                disk is None and line.startswith("/dev/")
            ):
                data = line.split()
                if data[0] in devs:
                    # Make sure to count each block device only one time
                    # some filesystems eg btrfs have multiple entries
                    continue
                total += int(data[1]) / 1024 / 1024
                used += int(data[2]) / 1024 / 1024
                free += int(data[3]) / 1024 / 1024
                devs.append(data[0])

        if total == 0:
            return free, used, "err", total

        return free, used, 100 * used / total, total

    def _get_diskstats(self, disk):
        read, write = 0, 0

        if disk and disk.startswith("/dev/"):
            disk = disk[5:]

        with Path("/proc/diskstats").open() as fd:
            for line in fd:
                data = line.split()
                if disk:
                    if data[2] == disk:
                        read += int(data[5]) * self.sector_size
                        write += int(data[9]) * self.sector_size
                else:
                    if data[1] == "0":
                        read += int(data[5]) * self.sector_size
                        write += int(data[9]) * self.sector_size

        return read, write

    def _calc_diskstats(self, diskstats):
        current_time = time.perf_counter()
        timedelta = current_time - self.last_time
        read = (diskstats[0] - self.last_diskstats[0]) / timedelta
        write = (diskstats[1] - self.last_diskstats[1]) / timedelta
        total = read + write
        self.last_diskstats = diskstats
        self.last_time = current_time

        return read, write, total

    def diskdata(self):
        disk_data = {"disk": self.disk_name}
        threshold_data = disk_data.copy()

        if self.init["df"]:
            df_usages = self._get_df_usages(self.disk)
            data = dict(zip(self.init["df"]["keys"], df_usages))
            threshold_data.update(data)

            for x in self.init["df"]["placeholders"]:
                disk_data[x] = self.py3.safe_format(
                    self.format_space, {"value": data[x]}
                )

        if self.init["diskstats"]:
            diskstats = self._calc_diskstats(self._get_diskstats(self.disk))
            data = dict(zip(self.init["diskstats"]["keys"], diskstats))
            threshold_data.update(data)

            for x in self.init["diskstats"]["placeholders"]:
                value, unit = self.py3.format_units(
                    data[x], unit=self.unit, si=self.si_units
                )
                disk_data[x] = self.py3.safe_format(
                    self.format_rate, {"value": value, "unit": unit}
                )

        for x in self.thresholds_init:
            if x in threshold_data:
                self.py3.threshold_get_color(threshold_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, disk_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
