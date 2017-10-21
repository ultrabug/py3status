# -*- coding: utf-8 -*-
"""
Display number of updates and more for Solus.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 3600)
    format: display format for this module (default 'UPD {update}')
    format_separator: show separator if more than one (default None)
    format_update: display format for updates (default None)
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {update} number of updates
    {format_update} format for updates

format_update placeholders:
    {name} package name, eg py3status
    {version} package version, eg 3.7
    {release} package release, eg 1

Color thresholds:
    update: print a color based on number of updates

Requires:
    eopkg requires root privileges to update repository databases.
    We can schedule a hourly timer service with systemd using the
    files below. Make sure to enable the timer service.

    | File 1: /etc/systemd/system/py3status-eopkg_updates.service
    | ------------------------------------------------------------
    | [Unit]
    | Description=Updates eopkg repositories
    |
    | [Service]
    | Type=oneshot
    | ExecStart=/usr/bin/eopkg update-repo

    | File 2: /etc/systemd/system/py3status-eopkg_updates.timer
    | ----------------------------------------------------------
    | [Unit]
    | Description=Updates eopkg repositories every hour
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
solus_updates {
    color_steelblue = '#5fafff'
    color_hotpink = '#ff5fd7'
}

# show 'UPDATE AVAILABLE'
solus_updates {
    format = '\?if=update&color=steelblue AVAILABLE UPDATE'
}

show UPD and count
solus_updates {
    format = '[\?not_zero [\?color=steelblue&show \u26ca] '
    format += '[\?color=hotpink {update}]]'
}

# show count and names
solus_updates {
    format = '[\?not_zero&color=hotpink UPD {update}][: {format_update}]'
    format_update = '\?color=steelblue {name}'
    format_separator = ' '
}

# show update bars
solus_updates {
    format = 'UPD {format_update}'
    format_update = '\?color=steelblue \|'
}

# show count thresholds
solus_updates {
    format = '[\?not_zero [\?color=update&show UPD] {update}]'
    thresholds = [(10, 'good'), (20, 'degraded'), (30, 'bad')]
}
```

SAMPLE OUTPUT
{'full_text': 'UPD 26'}
"""

STRING_NOT_INSTALLED = 'eopkg not installed'
EOPKG_COMMAND = ['eopkg', 'list-upgrades', '--long']


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 3600
    format = 'UPD {update}'
    format_separator = None
    format_update = None
    thresholds = []

    def post_config_hook(self):
        if not self.py3.check_commands(EOPKG_COMMAND[0]):
            raise Exception(STRING_NOT_INSTALLED)
        if not self.format_separator:
            self.format_separator = ''

    def solus_updates(self):
        eopkg_data = self.py3.command_output(EOPKG_COMMAND).split('\n\n')
        format_update = None
        count_update = 0

        new_eopkg = []
        for chunk in eopkg_data:
            if chunk.startswith('Name:'):
                new_eopkg.append(chunk)
                count_update += 1

        if self.format_update and new_eopkg:
            new_data = []
            for update in new_eopkg:
                header = update.splitlines()[0].split(',')
                new_data.append(self.py3.safe_format(
                    self.format_update, {
                        'name': header[0].split(':')[-1],
                        'version': header[1].split(':')[-1],
                        'release': header[2].split(':')[-1],
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
