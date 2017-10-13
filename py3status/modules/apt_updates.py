# -*- coding: utf-8 -*-
"""
Display numbers of updates and more for Debian-based distributions.

Configuration parameters:
    apt_get: specify upgrade or dist-upgrade to use (default 'upgrade')
    cache_timeout: refresh interval for this module (default 3600)
    format: display format for this module (default 'UPD {update}')
    format_install: display format for packages (default None)
    format_install_separator: show separator if more than one (default None)
    format_keep: display format for packages (default None)
    format_keep_separator: show separator if more than one (default None)
    format_remove: display format for packages (default None)
    format_remove_separator: show separator if more than one (default None)
    format_unmet: display format for packages (default None)
    format_unmet_separator: show separator if more than one (default None)
    format_upgrade: display format for packages (default None)
    format_upgrade_separator: show separator if more than one (default None)
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {format_keep}    format for packages to be kept back
    {format_install} format for new packages to install
    {format_remove}  format for packages to remove
    {format_unmet}   format for packages with unmet dependencies
    {format_upgrade} format for packages to upgrade
    {keep}           number of packages to be kept back
    {install}        number of new packages to install
    {remove}         number of packages to remove
    {unmet}          number of packages with unmet dependencies
    {upgrade}        number of packages to upgrade
    {update}         number of packages to install and/or upgrade

format_keep placeholders:
    {name}        package name, eg firefox
    {old_version} package version, eg 57.0~b7+build1-0ubuntu0.17.04.2
    {new_version} package new version, eg 57.0~b8+build3-0ubuntu0.17.04.1

format_install placeholders:
    {name}        package name, eg firefox
    {version}     package version, eg 57.0~b7+build1-0ubuntu0.17.04.2

format_remove placeholders:
    {name}        package name, eg firefox
    {version}     package version, eg 57.0~b7+build1-0ubuntu0.17.04.2

format_unmet placeholders:
    {name}        package name, eg python3.5
    {depends}     package dependency name, eg python3.5-minimal
    {wanted}      package dependency new version, eg 3.5.2-2ubuntu0~16.04.3
    {installed}   package dependency version, eg 3.5.2-2~16.01

format_upgrade placeholders:
    {name}        package name, eg firefox
    {old_version} package version, eg 57.0~b7+build1-0ubuntu0.17.04.2
    {new_version} package new version, eg 57.0~b8+build3-0ubuntu0.17.04.1

Color thresholds:
    keep:    a color based on number of packages to be kept back
    install: a color based on number of new packages to install
    remove:  a color based on number of packages to remove
    unmet:   a color based on number of packages with unmet dependencies
    upgrade: a color based on number of packages to upgrade
    update:  a color based on number of packages to install and/or upgrade

Requires:
    apt-get: a package manager

Note 1:
    We can refresh a module using `py3-cmd` command.
    An excellent example of using this command in a dpkg hook.

    | /etc/apt/apt.conf.d/99py3status-apt_updates
    | --------------------------------------------
    | DPkg::Post-Invoke {'echo Signaling apt_updates module...';};
    | DPkg::Post-Invoke {'py3-cmd refresh apt_updates';};

Note 2:
    The command 'apt-get autoremove' is used to remove packages that were
    automatically installed to satisfy dependencies for other packages and
    are now no longer needed.

@author lasers

Examples:
```
# show new packages
apt_updates {
    format = '[\?max_length=999&color=degraded {format_install}] {update}'
    format_install = '{name}'
    format_install_separator = ' '
}

# show remove packages
apt_updates {
    format = '[\?max_length=999&color=bad {format_remove}] {update}'
    format_remove = '{name}'
    format_remove_separator = ' '
}

# show all counts
apt_updates {
    format = '[\?color=bad&show REMOVE] {remove} '
    format += '[\?color=#fa0&show KEEP] {keep} '
    format += '[\?color=degraded&show INSTALL] {install} '
    format += '[\?color=good&show UPGRADE] {upgrade} '
    format += '[\?color=#0ff&show UPDATE] {update}'
}

# show bar colors based on numbers of packages
apt_updates {
    format = '[{format_unmet}][{format_remove}][{format_install}]'
    format += '[{format_keep}][{format_upgrade}]'
    format_unmet = '\?color=#aaf\|'
    format_remove = '\?color=bad \|'
    format_keep = '\?color=#fa0 \|'
    format_install = '\?color=degraded \|'
    format_upgrade = '\?color=good \|'
}

# show count thresholds
apt_updates {
    format = '[\?not_zero [\?color=update&show UPD] {update}]'
    thresholds = [(10, 'good'), (20, 'degraded'), (30, 'bad')]
}

# show unmet dependencies
apt_updates {
    format = '[\?if=unmet&color=bad UNMET DEPENDENCIES] [{format_unmet}]'
    format_unmet = '{name}'
    format_unmet_separator = '\?color=bad , '
}

# reminder: you can replace UPD with an icon and/or mix things together
# such as using bars and still print names for install+removal packages, etc.
apt_updates {
    format = '\u26ca'  # shogi piece, turned black
}

# reminder: you can mix some things together, eg using keep+upgrade bars and
# print names for install+removal packages, preferably in different colors too.
apt_updates {
    format = '[\?max_length=999&color=bad {format_remove}][\?soft  ]'
    format += '[\?max_length=999&color=degraded {format_install}]'
    format += '[{format_keep}][{format_upgrade}] {update}'
    format_remove = '{name}'
    format_remove_separator = ' '
    format_install = '{name}'
    format_install_separator = ' '
    format_keep = '\?color=#fa0 \|'
    format_upgrade = '\?color=good \|'
}

# add your snippets here
apt_updates {
    format = '...'
}
```

SAMPLE OUTPUT
{'full_text': 'UPD 5'}
"""

STRING_NOT_INSTALLED = 'not installed'


class Py3status:
    """
    """
    # available configuration parameters
    apt_get = 'upgrade'
    cache_timeout = 3600
    format = 'UPD {update}'
    format_install = None
    format_install_separator = None
    format_keep = None
    format_keep_separator = None
    format_remove = None
    format_remove_separator = None
    format_unmet = None
    format_unmet_separator = None
    format_upgrade = None
    format_upgrade_separator = None
    thresholds = []

    def post_config_hook(self):
        if not self.py3.check_commands(['apt-get']):
            raise Exception(STRING_NOT_INSTALLED)
        if self.apt_get not in ['upgrade', 'dist-upgrade']:
            raise Exception('incorrect apt_get')
        self.apt_get = ['apt-get', self.apt_get, '--simulate', '-V']
        self.operation = ('Inst', 'Conf', 'Remv')

        if not self.format_keep_separator:
            self.format_keep_separator = ''
        if not self.format_install_separator:
            self.format_install_separator = ''
        if not self.format_remove_separator:
            self.format_remove_separator = ''
        if not self.format_unmet_separator:
            self.format_unmet_separator = ''
        if not self.format_upgrade_separator:
            self.format_upgrade_separator = ''

        self.apt = {
            'keep': {
                'action': 'have been kept back',
                'boolean': self.py3.format_contains(
                    self.format, ['format_keep']) and self.format_keep,
                'format': self.format_keep,
                'separator': self.format_keep_separator,
            },
            'install': {
                'action': 'will be installed',
                'boolean': self.py3.format_contains(
                    self.format, ['format_install']) and self.format_install,
                'format': self.format_install,
                'separator': self.format_install_separator,
            },
            'remove': {
                'action': 'no longer required',
                'boolean': self.py3.format_contains(
                    self.format, ['format_remove']) and self.format_remove,
                'format': self.format_remove,
                'separator': self.format_remove_separator,
            },
            'unmet': {
                'action': 'have unmet dependencies',
                'boolean': self.py3.format_contains(
                    self.format, ['format_unmet']) and self.format_unmet,
                'format': self.format_unmet,
                'separator': self.format_unmet_separator,
            },
            'upgrade': {
                'action': 'will be upgraded',
                'boolean': self.py3.format_contains(
                    self.format, ['format_upgrade']) and self.format_upgrade,
                'format': self.format_upgrade,
                'separator': self.format_upgrade_separator,
            },
        }

    def apt_updates(self):
        data = {}
        count = {}
        format = {}
        new_data = {}

        apt_updates = self.py3.command_output(self.apt_get)

        for chunk in apt_updates.split('The following ')[1:]:
            chunk = chunk.splitlines()
            for key in self.apt:
                if self.apt[key]['action'] in chunk[0]:
                    data[key] = chunk[1:]

        for key in self.apt:
            count[key] = 0
            if key in data:
                new_data[key] = []
                for line in data[key]:
                    if key == 'unmet' and not line[0].isspace():
                        continue
                    elif not line[:3].isspace():
                        continue
                    elif line.startswith(self.operation):
                        break
                    count[key] += 1

                    if self.apt[key]['boolean']:
                        if key == 'unmet':
                            line = line.replace(':', '').replace('=', '')
                        line = line.replace('(', '').replace(')', '').split()
                        package = {'name': line[0]}
                        if key in ['install', 'remove']:
                            package['version'] = line[1]
                        elif key == 'unmet':
                            package['depends'] = line[2]
                            package['wanted'] = line[3]
                            package['installed'] = line[5]
                        else:
                            package['old_version'] = line[1]
                            package['new_version'] = line[3]

                        new_data[key].append(self.py3.safe_format(
                            self.apt[key]['format'], package))

                if self.apt[key]['boolean']:
                    format[key] = self.py3.composite_join(self.py3.safe_format(
                        self.apt[key]['separator']), new_data[key])

        count['update'] = count['install'] + count['upgrade']
        if self.thresholds:
            for k, v in count.items():
                self.py3.threshold_get_color(v, k)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {
                    'update': count['update'],
                    'keep': count['keep'],
                    'install': count['install'],
                    'remove': count['remove'],
                    'unmet': count['unmet'],
                    'upgrade': count['upgrade'],
                    'format_keep': format.get('keep'),
                    'format_install': format.get('install'),
                    'format_remove': format.get('remove'),
                    'format_unmet': format.get('unmet'),
                    'format_upgrade': format.get('upgrade'),
                })}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
