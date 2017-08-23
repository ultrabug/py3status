# -*- coding: utf-8 -*-
"""
Display number of updates and more for Void Linux.

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
    {version} package new version, eg 3.7_1
    {action} package action, eg update, install, configure, remove
    {arch} package architecture, eg x86_64, noarch
    {repository} package repository, eg https://repo.voidlinux.eu/current
    {installed_size} package installed size, eg 677KB
    {download_size} package download size, eg 141KB

Color thresholds:
    update: a color based on number of updates

Requires:
    cronie: runs specified programs at scheduled times

    xbps-install needs root privileges to synchronize remote repository
    index files. We can schedule a hourly cronjob with cronie using the
    file below. Make sure to enable the cronie service too.

    | /etc/cron.hourly/1xbps-install-sync
    | -----------------------------------
    | #!/bin/sh
    | /usr/bin/xbps-install --sync

@author lasers

Examples:
```
add colors
void_updates {
    color_viridian = '#478061'
    color_norway = '#ADC3AD'
}

# show UPDATE
void_updates {
    format = '\?if=update&color=norway UPDATE'
}

show update shield with a count
void_updates {
    format = '[\?not_zero [\?color=viridian&show \u26ca] '
    format += '[\?color=norway {update}]]'
}

# show count and install names
void_updates {
    format = '[\?not_zero UPD {update}][: {format_update}]'
    format_update = '\?if=action=install&color=viridian {name}'
}

# show count and names
void_updates {
    format = '[\?not_zero UPD {update}][: {format_update}]'
    format_update = '\?color=norway {name}'
}

# show count and colorized names based on action
void_updates {
    format = '[\?not_zero UPD {update}][: {format_update}]'
    format_update = '[\?if=action=install&color=viridian {name}]'
    format_update += '[\?if=action=update&color=norway {name}]'
}

# show update bars
void_updates {
    format = '{format_update}'
    format_update = '[\?if=action=remove&color=bad \|]'
    format_update += '[\?if=action=configure&color=#fa0 \|]'
    format_update += '[\?if=action=install&color=degraded \|]'
    format_update += '[\?if=action=update&color=viridian \|]'
}

# show count thresholds
void_updates {
    format = '[\?not_zero [\?color=update&show UPD] {update}]'
    thresholds = [(0, 'good'), (20, 'degraded'), (30, 'bad')]
}
```

SAMPLE OUTPUT
{'full_text': 'UPD 14'}
"""

STRING_NOT_INSTALLED = 'not installed'
XBPS_COMMAND = ['xbps-install', '--update', '--dry-run']


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
        if not self.py3.check_commands(XBPS_COMMAND[0]):
            raise Exception(STRING_NOT_INSTALLED)
        if not self.format_separator:
            self.format_separator = ''

    def _human_bytes(self, size, precision=2):
        suffixes = ['B', 'KB', 'MB', 'GB']
        index, size = 0, int(size)
        while size > 1024:
            index += 1
            size /= 1024.0
        if index < 2:
            precision = 0
            size = round(size)
        return '%.*f%s' % (precision, size, suffixes[index])

    def void_updates(self):
        xbps_data = self.py3.command_output(XBPS_COMMAND).splitlines()
        count_update = len(xbps_data)
        format_update = None

        if self.format_update and xbps_data:
            new_data = []
            for line in xbps_data:
                package = line.split()
                name, version = package[0].rsplit('-', 1)
                installed_size = package[4]
                try:
                    download_size = package[5]
                except IndexError:
                    installed_size = None
                    download_size = package[4]

                new_data.append(self.py3.safe_format(
                    self.format_update, {
                        'name': name,
                        'version': version,
                        'action': package[1],
                        'arch': package[2],
                        'repository': package[3],
                        'installed_size': self._human_bytes(installed_size),
                        'download_size': self._human_bytes(download_size),
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
