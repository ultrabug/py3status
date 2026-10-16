r"""
Display drive temperatures.

Read drive temperatures natively from the kernel hwmon interface. SATA
drives report through the drivetemp driver and NVMe drives report through
the nvme driver. No daemon or subprocess is needed.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_drive}')
    format_drive: display format for drives
        (default '{name} [\?color=temp {temp}°C]')
    format_drive_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use for spinning hard disks
        (rotational) and solid state drives (solid), or a list to use for all
        drives *(default {'rotational': [(0, 'deepskyblue'), (25, 'good'),
        (41, 'degraded'), (46, 'bad')], 'solid': [(0, 'good'), (70, 'degraded'),
        (80, 'bad')]})*

Format placeholders:
    {format_drive} format for drives

format_drive placeholders:
    {name} name, eg ADATA SP550
    {device} device, eg sda, nvme0n1
    {temp} temperature, eg 44

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Bible of HDD failures:
    Hard disk temperatures higher than 45°C led to higher failure rates.
    Temperatures lower than 25°C led to higher failure rates as well.
    Aging hard disk drives (3 years and older) were much more prone to
    failure when their average temperatures were 40°C and higher.

    Hard disk manufacturers often state the operating temperatures of
    their hard disk drives to be between 0°C to 60°C. This can be misleading
    because what they mean is that your hard disk will function at these
    temperatures, but it doesn't tell you anything about how long they are
    going to survive at this range.

Backblaze:
    There is not a correlation between operating temperature and failure rates.
    The one exception is the Seagate Barracuda 1.5TB drives, which fail slightly
    more when they run warmer. As long as you run drives well within their
    allowed range of operating temperatures, keeping them cooler doesn’t matter.
    https://www.backblaze.com/blog/hard-drive-temperature-does-it-matter/

Examples:
```
# show device paths instead of names
drivetemp {
    format_drive = '/dev/{device} [\?color=temp {temp}°C]'
}

# show more colors
drivetemp {
    gradients = True
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'ADATA SP550 '}, {'color': '#00FF00', 'full_text': '25°C '},
    {'full_text': 'SanDisk SDSSDA240G '}, {'color': '#00FF00', 'full_text': '41°C'},
]

device
[
    {'full_text': '/dev/sda '}, {'color': '#00FF00', 'full_text': '35°C '},
    {'full_text': '/dev/nvme0n1 '}, {'color': '#FFFF00', 'full_text': '72°C'},
]
"""

import re
from pathlib import Path


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    format = "{format_drive}"
    format_drive = r"{name} [\?color=temp {temp}°C]"
    format_drive_separator = " "
    thresholds = {
        "rotational": [(0, "deepskyblue"), (25, "good"), (41, "degraded"), (46, "bad")],
        "solid": [(0, "good"), (70, "degraded"), (80, "bad")],
    }

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {"temp": ":.0f"},
                    "format_strings": ["format_drive"],
                }
            ],
        }

    def post_config_hook(self):
        self.hwmon_path = Path("/sys/class/hwmon")
        self.sata_info = {}
        self.thresholds_kind = {}
        if isinstance(self.thresholds, dict) and "temp" not in self.thresholds:
            for kind in ("rotational", "solid"):
                if kind in self.thresholds:
                    self.thresholds_kind[kind] = ("temp", kind, sorted(self.thresholds[kind]))
        self.thresholds_init = self.py3.get_color_names_list(self.format_drive)

    def _get_block_name(self, hwmon, device):
        if hwmon == "nvme":
            names = [x.name for x in device.glob("nvme*n*") if x.is_dir()]
        else:
            names = [x.name for x in (device / "block").iterdir()]
        return min(names, default=None)

    def _get_sata_info(self, device, block):
        try:
            dev = (device / "block" / block / "dev").read_text().strip()
            udev = Path("/run/udev/data", f"b{dev}")
            # udev rewrites this file when a disk is added, eg swapped
            mtime = udev.stat().st_mtime_ns
            cached = self.sata_info.get(dev)
            if cached and cached[0] == mtime:
                return cached[1:]
            data = udev.read_text()
        except OSError:
            return None, self._get_kind(block)
        model = None
        for line in data.splitlines():
            if line.startswith("E:ID_MODEL_ENC="):
                model = line.split("=", 1)[1]
                model = re.sub(r"\\x([0-9a-fA-F]{2})", lambda x: chr(int(x[1], 16)), model)
                model = model.strip()
                break
        kind = self._get_kind(block)
        self.sata_info[dev] = (mtime, model, kind)
        return model, kind

    def _get_kind(self, block):
        try:
            rotational = Path("/sys/class/block", block, "queue", "rotational").read_text()
        except OSError:
            return "solid"
        return "rotational" if rotational.strip() == "1" else "solid"

    def _get_drives(self):
        drives = []
        for path in sorted(self.hwmon_path.iterdir()):
            try:
                hwmon = (path / "name").read_text().strip()
                if hwmon not in ("drivetemp", "nvme"):
                    continue
                device = path / "device"
                block = self._get_block_name(hwmon, device)
                name = (device / "model").read_text().strip()
                kind = "solid"
                if hwmon == "drivetemp" and block:
                    # sysfs cuts SATA models to 16 characters, udev has them in full
                    model, kind = self._get_sata_info(device, block)
                    name = model or name
                drives.append(
                    {
                        "name": name,
                        "device": block or "",
                        "temp": int((path / "temp1_input").read_text()) / 1000,
                        "kind": kind,
                    }
                )
            except (OSError, ValueError):
                continue
        return sorted(drives, key=lambda x: x["device"])

    def drivetemp(self):
        new_drive = []
        for drive in self._get_drives():
            for x in self.thresholds_init:
                if x in drive:
                    name = self.thresholds_kind.get(drive["kind"], x) if x == "temp" else x
                    self.py3.threshold_get_color(drive[x], name)

            new_drive.append(self.py3.safe_format(self.format_drive, drive))

        format_drive_separator = self.py3.safe_format(self.format_drive_separator)
        format_drive = self.py3.composite_join(format_drive_separator, new_drive)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"format_drive": format_drive}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
