# -*- coding: utf-8 -*-
"""
Display disk information.

Configuration parameters:
    cache_timeout: refresh interval for this module. (default 10)
    disks: mountpoints, disks or partitions list to show stats
        for, i.e. `["sda1", "/home", "/dev/sdd"]`.
        None for all disks.
        (default [])
    format: display format for this module.
        (default "{disk}: {used_percent}% ({total})")
    format_rate: display format for rates value
        (default "[\?min_length=11 {value:.1f} {unit}]")
    format_space: display format for disk space values
        (default "[\?min_length=5 {value:.1f}]")
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

from __future__ import division  # python2 compatibility

from collections import namedtuple
import os
from time import time


Mount = namedtuple("Mount", ["device", "mountpoint"])
Disk = namedtuple("Disk", ["device", "name"])
Df = namedtuple("Df", ["device", "blocks", "used", "free", "perc", "mountpoint"])
Diskstat = namedtuple("Diskstat", ["minor", "device", "read", "written"])


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    disks = []
    format = "{disk}: {used_percent}% ({total})"
    format_rate = "[\?min_length=11 {value:.1f} {unit}]"
    format_space = "[\?min_length=5 {value:.1f}]"
    si_units = False
    thresholds = {
        "free": [(0, "bad"), (10, "degraded"), (100, "good")],
        "total": [(0, "good"), (1024, "degraded"), (1024 * 1024, "bad")],
        "used_percent": [(0, "good"), (40, "degraded"), (75, "bad")],
    }
    unit = "B/s"

    class Meta:
        deprecated = {
            "remove": [{"param": "sector_size", "msg": "obsolete parameter"}],
            "rename": [
                {"param": "disk", "new": "disks", "msg": "rename parameter to `disks`"}
            ],
        }

    def _resolve_disk_name(self, path):
        disk_path = os.path.realpath(path)
        return os.path.basename(disk_path)

    def _get_sector_size(self, drive):
        basename = self._resolve_disk_name(drive)
        block_device = os.path.realpath("/sys/class/block/" + basename)
        if not block_device.endswith("block/" + basename):
            block_device = os.path.dirname(block_device)
        with open("{}/queue/hw_sector_size".format(block_device)) as ss:
            out = int(ss.read().strip())
        return out

    def _add_monitored_disk(self, path):
        basename = self._resolve_disk_name(path)
        if os.path.exists("/dev/" + basename):
            self._disks.add(Disk(device="/dev/" + basename, name=basename))

    def _get_all_disks(self):
        with open("/proc/diskstats") as ds:
            for stat in ds:
                line = stat.split()
                if int(line[1]) == 0:
                    self._add_monitored_disk("/dev/" + line[2])

    def post_config_hook(self):
        """
        Format of total, up and down placeholders under self.format.
        As default, substitutes self.left_align and self.precision as %s and %s
        Placeholders:
            value - value (float)
            unit - unit (string)
        """
        # deprecation
        if self.disks is None:
            self.disks = []
        elif not isinstance(self.disks, list):
            self.disks = [self.disks]

        self._disks = set()

        if not self.disks:
            self._all = True
            self._get_all_disks()
        else:
            with open("/proc/mounts") as mounts:
                mounts = [Mount(*x.split()[:2]) for x in mounts.readlines()]
            for item in self.disks:
                # mountpoint or fully qualified device path
                if item.startswith("/"):
                    # mountpoint
                    if not item.startswith("/dev/"):
                        for mount in mounts:
                            if mount.mountpoint == item:
                                self._add_monitored_disk(mount.device)
                    else:
                        self._add_monitored_disk(item)

                # non fully qualified device path
                else:
                    self._add_monitored_disk("/dev/" + item)
            if not self._disks:
                self._all = True
                self._get_all_disks()
            else:
                self._all = False

        self.last_diskstats = self._get_diskstats()
        self.last_time = time()

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def diskdata(self):
        self.values = {
            "disk": ",".join(d.name for d in self._disks) if not self._all else "all"
        }
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

        disk_names = {d.name: d.device for d in self._disks}
        _df = self.py3.command_output("df")
        # loop on df output minus header line
        for line in _df.splitlines()[1:]:
            df = Df(*line.split())
            if (
                not self._all
                and (
                    self._resolve_disk_name(df.device) in disk_names
                    or any(df.device.startswith(x) for x in disk_names.values())
                )
            ) or (self._all and df.device.startswith("/dev/")):
                if df.device in devs:
                    # Make sure to count each block device only one time
                    # some filesystems eg btrfs have multiple entries
                    continue
                total += int(df.blocks) / 1024 / 1024
                used += int(df.used) / 1024 / 1024
                free += int(df.free) / 1024 / 1024
                devs.append(df.device)

        if total == 0:
            return free, used, "err", total

        return free, used, 100 * used / total, total

    def _get_diskstats(self):
        read = 0
        write = 0
        disk_names = [d.name for d in self._disks]
        with open("/proc/diskstats", "r") as fd:
            for line in fd:
                data = line.split()
                stat = Diskstat(data[1], data[2], data[5], data[9])
                if not self._all:
                    if stat.device in disk_names:
                        read += int(stat.read) * self._get_sector_size(stat.device)
                        write += int(stat.written) * self._get_sector_size(stat.device)
                elif stat.minor == "0":
                    read += int(stat.read) * self._get_sector_size(stat.device)
                    write += int(stat.written) * self._get_sector_size(stat.device)

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
    config = {"disks": "sda"}
    from py3status.module_test import module_test

    module_test(Py3status, config=config)
