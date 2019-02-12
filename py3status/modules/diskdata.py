# -*- coding: utf-8 -*-
"""
Display disk information.

Configuration parameters:
    cache_timeout: refresh interval for this module. (default 10)
    disk: mountpoints, disks or partitions list to show stats
        for, i.e. `["sda1", "/home", "/dev/sdd"]`.
        None for all disks, filtered by `type` parameter.
        (default None)
    format: display format for this module.
        (default "{disk}: {used_percent}% ({total})")
    format_rate: display format for rates value
        (default "[\?min_length=11 {value:.1f} {unit}]")
    format_space: display format for disk space values
        (default "[\?min_length=5 {value:.1f}]")
    sector_size: size of the disk's sectors (normally taken from sysfs).
        (default None)
    si_units: use SI units
        (default False)
    thresholds: specify color thresholds to use
        *(default {'free': [(0, 'bad'), (10, 'degraded'), (100, 'good')],
        'total': [(0, 'good'), (1024, 'degraded'), (1024 * 1024, 'bad')],
        'used_percent': [(0, 'good'), (40, 'degraded'), (75, 'bad')]})*
    types: list of device types to include in "all disks mode".
        Supported values: `disks` for PATA/SATA disks, `raid` for raid devices,
        `cdrom` for cdroms, `mmc` for memory cards.
        (default ['disks'])
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

from __future__ import division  # python2 compatibility
from time import time
import os


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    disk = None
    format = "{disk}: {used_percent}% ({total})"
    format_rate = "[\?min_length=11 {value:.1f} {unit}]"
    format_space = "[\?min_length=5 {value:.1f}]"
    sector_size = None
    si_units = False
    thresholds = {
        "free": [(0, "bad"), (10, "degraded"), (100, "good")],
        "total": [(0, "good"), (1024, "degraded"), (1024 * 1024, "bad")],
        "used_percent": [(0, "good"), (40, "degraded"), (75, "bad")],
    }
    types = ["disks"]
    unit = "B/s"

    def _resolve_disk_name(self, path):
        disk_path = os.path.realpath(path)
        return os.path.basename(disk_path)

    def _add_monitored_disk(self, path):
        basename = self._resolve_disk_name(path)
        if not self.sector_size:
            with open("/sys/block/{}/queue/hw_sector_size".format(basename)) as ss:
                sector_size = int(ss.read().strip())
        self._disks[basename] = sector_size

    def post_config_hook(self):
        """
        Format of total, up and down placeholders under self.format.
        As default, substitutes self.left_align and self.precision as %s and %s
        Placeholders:
            value - value (float)
            unit - unit (string)
        """
        # deprecation
        if self.disk is None:
            self.disk = []
        elif not isinstance(self.disk, list):
            self.disk = [self.disk]
        types_info = {
            "disks": {"major": [3, 8, 22]},
            "raid": {"major": [9]},
            "cdrom": {
                "major": [
                    11,
                    15,
                    16,
                    17,
                    18,
                    20,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    32,
                    33,
                    34,
                ]
            },
            "mmc": {"major": [31]},
        }

        self._disks = {}

        if not self.disk:
            allowed_types = set()
            for _type in self.types:
                allowed_types.update(types_info[_type]["major"])
            with open("/proc/diskstats") as ds:
                for stat in ds:
                    line = stat.split()
                    if int(line[0]) in allowed_types and int(line[1]) == 0:
                        self._add_monitored_disk("/dev/" + line[2])
        else:
            for disk in self.disk.split():
                # mountpoint or fully qualified device path
                if disk.startswith("/"):
                    # mountpoint
                    if not disk.startswith("/dev/"):
                        with open("/proc/mounts") as mounts:
                            for entry in mounts:
                                mount = entry.split()
                                if mount[1] == disk:
                                    self._add_monitored_disk(mount[0])
                    else:
                        self._add_monitored_disk(disk)

                # non fully qualified device path
                else:
                    self._add_monitored_disk("/dev/" + disk)

        self.last_diskstats = self._get_diskstats()
        self.last_time = time()

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def diskdata(self):
        self.values = {"disk": ",".join(self._disks.keys())}
        threshold_data = {}

        if self.py3.format_contains(self.format, ["read", "write", "total"]):
            diskstats = self._get_diskstats()
            current_time = time()

            timedelta = current_time - self.last_time
            read = (diskstats[0] - self.last_diskstats[0]) / timedelta
            write = (diskstats[1] - self.last_diskstats[1]) / timedelta
            total = read + write

            self.last_diskstats = diskstats
            self.last_time = current_time

            self.values["read"] = self._format_rate(read)
            self.values["total"] = self._format_rate(total)
            self.values["write"] = self._format_rate(write)
            threshold_data.update({"read": read, "write": write, "total": total})

        if self.py3.format_contains(self.format, ["free", "used*", "total_space"]):
            free, used, used_percent, total_space = self._get_free_space()

            self.values["free"] = self.py3.safe_format(
                self.format_space, {"value": free}
            )
            self.values["used"] = self.py3.safe_format(
                self.format_space, {"value": used}
            )
            self.values["used_percent"] = self.py3.safe_format(
                self.format_space, {"value": used_percent}
            )
            self.values["total_space"] = self.py3.safe_format(
                self.format_space, {"value": total_space}
            )
            threshold_data.update(
                {"free": free, "used": used, "used_percent": used_percent}
            )

        for x in self.thresholds_init:
            if x in threshold_data:
                self.py3.threshold_get_color(threshold_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, self.values),
        }

    def _get_free_space(self):

        total = 0
        used = 0
        free = 0
        devs = []

        df = self.py3.command_output("df")
        for line in df.splitlines():
            data = line.split()
            if self._resolve_disk_name(data[0]) in self._disks or any(
                data[0] == "/dev/" + x for x in self._disks
            ):
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

    def _get_diskstats(self):
        read = 0
        write = 0
        with open("/proc/diskstats", "r") as fd:
            for line in fd:
                data = line.split()
                if data[2] in self._disks:
                    read += int(data[5]) * self._disks[data[2]]
                    write += int(data[9]) * self._disks[data[2]]
        return read, write

    def _format_rate(self, value):
        """
        Return formatted string
        """
        value, unit = self.py3.format_units(value, unit=self.unit, si=self.si_units)
        return self.py3.safe_format(self.format_rate, {"value": value, "unit": unit})


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
