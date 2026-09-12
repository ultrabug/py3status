# I3S_CONTAINER_TYPE must match py3status/modules/i3status.py's filename.
# I3S_PROXY_TYPE has no file (see py3status/i3status/proxy.py) and just
# needs to stay distinct, since that's how core tells a container from a proxy.
I3S_CONTAINER_TYPE = "i3status"
I3S_PROXY_TYPE = "i3status_proxy"

# module name classification
I3S_INSTANCE_MODULES = [
    "battery",
    "cpu_temperature",
    "disk",
    "ethernet",
    "path_exists",
    "read_file",
    "run_watch",
    "tztime",
    "volume",
    "wireless",
]

I3S_SINGLE_NAMES = ["cpu_usage", "ddate", "ipv6", "load", "memory", "time"]

I3S_MODULE_NAMES = I3S_SINGLE_NAMES + I3S_INSTANCE_MODULES

# display defaults for "time"/"tztime"; the container is always forced to
# I3S_TZTIME_FORMAT so a raw reading carries a timezone to extract (see
# proxy.py's _set_time_zone).
I3S_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
I3S_TZTIME_FORMAT = f"{I3S_TIME_FORMAT} %Z"

# time/tztime module name -> its default display format; also doubles as
# the membership set for "is this a time-style module" checks
I3S_TIME_MODULES = {"time": I3S_TIME_FORMAT, "tztime": I3S_TZTIME_FORMAT}

# general.interval when the user never set one explicitly
DEFAULT_GENERAL_INTERVAL = 5

# a bare "i3status { }" gets this instead of dying - copied
# from upstream's sample config minus redundancies.
DEFAULT_ITEMS = [
    {"name": "ipv6"},
    {"name": "wireless _first_", "format_up": "W: (%quality at %essid) %ip"},
    {"name": "ethernet _first_"},
    {"name": "battery all"},
    {"name": "disk /", "format": "%avail"},
    {"name": "load", "format": "%1min"},
    {
        "name": "memory",
        "format": "%used | %available",
        "threshold_degraded": "1G",
        "format_degraded": "MEMORY < %available",
    },
    {"name": "tztime local", "format": I3S_TIME_FORMAT},
]
