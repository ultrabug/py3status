# -*- coding: utf-8 -*-
"""
Display number of updates and more for Alpine Linux.

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
    {new_version} package version, eg 3.8.0
    {new_release} package release, eg 0
    {old_version} package old version, 3.7.0
    {old_release} package old release, eg 1

Color thresholds:
    update: a color based on number of updates

Requires:
    apk needs root privileges to update repository indexes from remote
    repositories. We can schedule a hourly cron using the file below.

    | /etc/periodic/hourly/py3status-apk_updates
    | -------------------------------------------
    | #!/bin/sh
    | /sbin/apk update --quiet

@author lasers

Examples:
```
# add colors
alpine_updates {
    color_alpine = '#0D597F'
}

# show UPDATE
alpine_updates {
    format = '\?if=update&color=alpine UPDATE'
}

# show update shield with a count
alpine_updates {
    format = '[\?not_zero [\?color=alpine&show \u26ca] {update}]'
}

# show count and names
alpine_updates {
    format = '[\?not_zero&color=alpine UPD {update}][: {format_update}]'
    format_update = '\?color=alpine {name}'
}

# show update bars
alpine_updates {
    format = '{format_update}'
    format_update = '[\?color=alpine \|]'
}

# show count thresholds
alpine_updates {
    format = '[\?not_zero [\?color=update&show UPD] {update}]'
    thresholds = [(0, 'good'), (20, 'degraded'), (30, 'bad')]
}
```

SAMPLE OUTPUT
{'full_text': 'UPD 13'}
"""

STRING_NOT_INSTALLED = 'apk not installed'
APK_COMMAND = ['apk', 'version', '-l', '"<"']


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
        if not self.py3.check_commands(APK_COMMAND[0]):
            raise Exception(STRING_NOT_INSTALLED)
        if not self.format_separator:
            self.format_separator = ''

    def alpine_updates(self):
        apk_data = self.py3.command_output(APK_COMMAND).splitlines()[1:]
        count_update = len(apk_data)
        format_update = None

        if self.format_update and apk_data:
            new_data = []
            for line in apk_data:
                package = [x.strip() for x in line.split('<')]
                pkg_string, old_release = package[0].rsplit('-r')
                new_version, new_release = package[1].rsplit('-r')
                name, old_version = pkg_string.rsplit('-', 1)

                new_data.append(self.py3.safe_format(
                    self.format_update, {
                        'name': name,
                        'new_version': new_version,
                        'new_release': new_release,
                        'old_version': old_version,
                        'old_release': old_release,
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
