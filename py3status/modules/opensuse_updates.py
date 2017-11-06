# -*- coding: utf-8 -*-
"""
Display number of updates and more for openSUSE.

Configuration parameters:
    all: list all packages for which newer versions are available,
        regardless whether they are installable or not (default False)
    cache_timeout: refresh interval for this module (default 3600)
    format: display format for this module (default 'UPD {update}')
    format_separator: show separator if more than one (default None)
    format_update: display format for updates (default None)
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {update} number of updates
    {format_update} format for updates

format_update placeholders:
    {status} package status, eg i, v, .l
    {repository} package repository, eg openSUSE-20171018-0
    {name} package name, eg py3status
    {current} package current version, eg 3.7.0
    {available} package available version, eg 3.8.0
    {arch} package architecture, eg x86_64

Color thresholds:
    update: a color based on number of updates

Requires:
    zypper needs root privileges to refresh the repositories.
    We can schedule a hourly timer service with systemd using
    the files below. Make sure to enable the timer service.

    | File 1: /etc/systemd/system/py3status-zypper_updates.service
    | -------------------------------------------------------------
    | [Unit]
    | Description=Updates zypper repositories
    |
    | [Service]
    | Type=oneshot
    | ExecStart=/usr/bin/zypper refresh

    | File 2: /etc/systemd/system/py3status-zypper_updates.timer
    | -----------------------------------------------------------
    | [Unit]
    | Description=Updates zypper repositories every hour
    |
    | [Timer]
    | OnCalendar=hourly
    | RandomizedDelaySec=5m
    |
    | [Install]
    | WantedBy=timers.target

@author lasers

Examples:
```
# add colors
opensuse_updates {
    color_good = '#73ba25'
    color_bad = '#CE4E29'
    color_degraded = '#E9F981'
}

# show 'UPDATE AVAILABLE'
opensuse_updates {
    format = '\?if=update&color=good UPDATE AVAILABLE'
}

# show update shield with a count
opensuse_updates {
    format = '[\?not_zero [\?color=suse&show \u26ca] {update}]'
}

# show count and names
opensuse_updates {
    format = '[\?not_zero&color=good UPD {update}][: {format_update}]'
    format_update = '\?color=good {name}'
}

# show update bars
opensuse_updates {
    format = '[{format_update}]'
    format_update = '\?color=good \|'
}

# show count thresholds
opensuse_updates {
    format = '[\?not_zero [\?color=update&show UPD] {update}]'
    thresholds = [(0, 'good'), (20, 'degraded'), (30, 'bad')]
}
```

SAMPLE OUTPUT
{'full_text': 'UPD 45'}
"""

STRING_NOT_INSTALLED = 'zypper not installed'


class Py3status:
    """
    """
    # available configuration parameters
    all = False
    cache_timeout = 3600
    format = 'UPD {update}'
    format_separator = None
    format_update = None
    thresholds = []

    def post_config_hook(self):
        self.zypper_command = ['zypper', 'list-updates']
        if self.all:
            self.zypper_command += ['--all']
        if not self.py3.check_commands(self.zypper_command[0]):
            raise Exception(STRING_NOT_INSTALLED)
        if not self.format_separator:
            self.format_separator = ''

    def opensuse_updates(self):
        zypper_data = self.py3.command_output(self.zypper_command)
        zypper_data = [x for x in zypper_data.splitlines() if x][4:]
        count_update = len(zypper_data)
        format_update = None

        if self.format_update and zypper_data:
            new_data = []
            for line in zypper_data:
                package = [x.strip() for x in line.split('|')]
                new_data.append(self.py3.safe_format(
                    self.format_update, {
                        'status': package[0],
                        'repository': package[1],
                        'name': package[2],
                        'current': package[3],
                        'available': package[4],
                        'arch': package[5],
                    }))

            format_separator = self.py3.safe_format(self.format_separator)
            format_update = self.py3.composite_join(format_separator, new_data)

        if self.thresholds:
            self.py3.threshold_get_color(count_update, 'update')

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {
                    'format_update': format_update,
                    'update': count_update
                })}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
