# -*- coding: utf-8 -*-
"""
Display number of updates and more for FreeBSD.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 3600)
    format: display format for this module (default 'UPD {update}')
    format_install: display format for packages (default None)
    format_install_separator: show separator if more than one (default None)
    format_remove: display format for packages (default None)
    format_remove_separator: show separator if more than one (default None)
    format_upgrade: display format for packages (default None)
    format_upgrade_separator: show separator if more than one (default None)
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {format_install} format for new packages to install
    {format_remove}  format for packages to remove
    {format_upgrade} format for packages to upgrade
    {install}        number of new packages to install
    {remove}         number of packages to remove
    {upgrade}        number of packages to upgrade
    {update}         number of packages to install and/or upgrade

format_install placeholders:
    {name}        package name, eg py3status
    {version}     package version, eg 3.8

format_remove placeholders:
    {name}        package name, eg py3status
    {version}     package version, eg 3.7

format_upgrade placeholders:
    {name}         package name, eg py3status
    {new_version}  package new version, eg 3.8
    {old_version}  package old version, eg 3.7

Color thresholds:
    install: a color based on number of new packages to install
    remove:  a color based on number of packages to remove
    upgrade: a color based on number of packages to upgrade
    update:  a color based on number of packages to install and/or upgrade

Requires:
    We need something to periodically refresh the repositories? UNKNOWN.

@author lasers

Examples:
```
# add colors
freebsd_updates {
    color_freebsd = '#ab2b28'
}

# show 'UPDATE AVAILABLE'
freebsd_updates {
    format = '\?if=update&color=freebsd AVAILABLE UPDATE'
}

show update shield and count
freebsd_updates {
    format = '[\?not_zero [\?color=freebsd&show \u26ca] {update}]]'
}

# show UPD count and names
freebsd_updates {
    format = '[\?not_zero&color=freebsd UPD {update}]'
    format += '[ {format_install}][ {format_upgrade}]'
    format_install = '{name}'
    format_upgrade = '{name}'
    format_install_separator = ' '
    format_upgrade_separator = ' '
}

# show install+update bars
freebsd_updates {
    format = 'UPD {format_install}{format_upgrade}"
    format_install = '\?color=freebsd \|'
    format_upgrade = '\?color=freebsd \|'
}

# show count thresholds
freebsd_updates {
    format = '[\?not_zero [\?color=update&show UPD] {update}]'
    thresholds = [(10, 'good'), (20, 'degraded'), (30, 'bad')]
}
```

SAMPLE OUTPUT
{'full_text': 'UPD 3'}
"""

STRING_NOT_INSTALLED = 'pkg not installed'
PKG_COMMAND = ['pkg', 'upgrade', '--dry-run', '--quiet']


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 3600
    format = 'UPD {update}'
    format_install = None
    format_install_separator = None
    format_remove = None
    format_remove_separator = None
    format_upgrade = None
    format_upgrade_separator = None
    thresholds = []

    def post_config_hook(self):
        if not self.py3.check_commands(PKG_COMMAND[0]):
            raise Exception(STRING_NOT_INSTALLED)
        if not self.format_install_separator:
            self.format_install_separator = ''
        if not self.format_remove_separator:
            self.format_remove_separator = ''
        if not self.format_upgrade_separator:
            self.format_upgrade_separator = ''

        self.pkg = {
            'install': {
                'action': 'INSTALLED:',
                'boolean': self.py3.format_contains(
                    self.format, ['format_install']) and self.format_install,
                'format': self.format_install,
                'separator': self.format_install_separator,
            },
            'remove': {
                'action': 'REMOVED:',
                'boolean': self.py3.format_contains(
                    self.format, ['format_remove']) and self.format_remove,
                'format': self.format_remove,
                'separator': self.format_remove_separator,
            },
            'upgrade': {
                'action': 'UPGRADED:',
                'boolean': self.py3.format_contains(
                    self.format, ['format_upgrade']) and self.format_upgrade,
                'format': self.format_upgrade,
                'separator': self.format_upgrade_separator,
            },
        }

    def freebsd_updates(self):
        data = {}
        count = {}
        format = {}
        new_data = {}

        pkg_data = self.py3.command_output(PKG_COMMAND)

        for chunk in pkg_data.split('\n\n')[1:]:
            chunk = chunk.splitlines()
            for key in self.pkg:
                if self.pkg[key]['action'] in chunk[0]:
                    data[key] = chunk[1:]

        for key in self.pkg:
            count[key] = 0
            if key in data:
                new_data[key] = []
                for line in data[key]:
                    count[key] += 1
                    if self.pkg[key]['boolean']:
                        line = line.split()
                        package = {}
                        if key in ['install', 'remove']:
                            name, version = line[0].rsplit('-', 1)
                            package['name'] = name
                            package['version'] = version
                        else:
                            package['name'] = line[0][:-1]
                            package['old_version'] = line[1]
                            package['new_version'] = line[3]
                        new_data[key].append(self.py3.safe_format(
                            self.pkg[key]['format'], package))

                if self.pkg[key]['boolean']:
                    format[key] = self.py3.composite_join(self.py3.safe_format(
                        self.pkg[key]['separator']), new_data[key])

        count['update'] = count['install'] + count['upgrade']
        if self.thresholds:
            for k, v in count.items():
                self.py3.threshold_get_color(v, k)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {
                    'update': count['update'],
                    'install': count['install'],
                    'remove': count['remove'],
                    'upgrade': count['upgrade'],
                    'format_install': format.get('install'),
                    'format_remove': format.get('remove'),
                    'format_upgrade': format.get('upgrade'),
                })}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
