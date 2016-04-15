
DEFAULT_I3STATUS_INTERVAL = 15

GENERAL_DEFAULTS = {
    'color_bad': '#FF0000',
    'color_degraded': '#FFFF00',
    'color_good': '#00FF00',
    'color_separator': '#333333',
    'colors': False,
    'interval': 5,
    'output_format': 'i3bar'
}

MAX_NESTING_LEVELS = 4

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

TZTIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'

TIME_MODULES = ['time', 'tztime']

I3STATUS_MODULES = [
    'battery', 'cpu_temperature', 'disk', 'ethernet', 'path_exists',
    'run_watch', 'tztime', 'volume', 'wireless'
]

I3S_SINGLE_NAMES = ['cpu_usage', 'ddate', 'ipv6', 'load', 'time']

ERROR_CONFIG = '''
    general {colors = true interval = 60}

    order += "static_string py3status"
    order += "tztime local"
    order += "group error"

    static_string py3status {format = "py3status"}
    tztime local {format = "%c"}
    group error{
        button_next = 1
        button_prev = 0
        fixed_width = False
        format = "{output}"
        static_string error_min {format = "CONFIG ERROR" color = "#FF0000"}
        static_string error {format = "$error" color = "#FF0000"}
}
'''
