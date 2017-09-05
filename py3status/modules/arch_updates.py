# -*- coding: utf-8 -*-
"""
Display numbers of updates and more for Arch Linux.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 3600)
    format: display format for this module (default 'UPD {update}')
    format_foreign: display format for foreign updates (default None)
    format_foreign_separator: show separator if more than one (default None)
    format_pacman: display format for pacman updates (default None)
    format_pacman_separator: show separator if more than one (default None)
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {update} number of updates
    {pacman} number of pacman updates
    {foreign} number of foreign updates
    {format_pacman} format for pacman updates
    {format_foreign} format for foreign updates

format_pacman placeholders:
    {name} package name, eg py3status
    {old_version} package old version, eg 3.7-1
    {new_version} package new version, eg 3.8-1

format_foreign placeholders:
    {name} package name, eg py3status
    {old_version} package old version, eg 3.8-1
    {new_version} package new version, eg 3.9-1

Color thresholds:
    update: print color based on number of updates
    pacman: print color based on number of pacman updates
    foreign: print color based on number of foreign updates

Requires:
    checkupdates (owned by pacman): safely print a list of pacman updates
    cower: a simple AUR downloader used to print a list of foreign updates

Note 1:
    We can refresh a module using `py3-cmd` command.
    An excellent example of using this command in a function.

    | ~/.{bash,zsh}{rc,_profile}
    | ---------------------------
    | function pacaur() {
    |     command pacaur "$@" && py3-cmd refresh arch_updates
    | }

Note 2:
    We can refresh a module using `py3-cmd` command.
    An excellent example of using this command in a pacman hook.

    | /usr/share/libalpm/hooks/py3status-arch-updates.hook
    | -----------------------------------------------------
    | [Trigger]
    | Operation = Install
    | Operation = Upgrade
    | Operation = Remove
    | Type = Package
    | Target = *
    |
    | [Action]
    | Description = Signaling arch_updates module...
    | When = PostTransaction
    | Exec = /usr/bin/py3-cmd refresh arch_updates

@author lasers

Examples:
```
# show update shield with count
arch_updates {
    format = '\?not_zero \u26ca {update}'
}

# show separate numbers of updates
arch_updates {
    format = '[\?if=update UPD [\?not_zero {pacman}]'
    format += '[\?soft , ][\?not_zero {foreign}]]'
}

# show PAC, FOR, or UPD with count
arch_updates {
    format = '[\?if=pacman [\?if=foreign UPD|PAC]'
    format += '|[\?if=foreign FOR]][\?not_zero  {update}]'
}

# show UPD with separate numbers of updates or show PAC or FOR with count
arch_updates {
    format = '[\?if=pacman [\?if=foreign UPD {pacman}, {foreign}'
    format += '|[\?not_zero PAC {update}]]|[\?not_zero FOR {update}]]'
}

# add colors
arch_updates {
    color_foreign = '#ffaa00'
    color_pacman = '#00aaff'
    color_update = '#80aa80'
}

# show UPD in a color and count
arch_updates {
    format = '[\?not_zero&color=pacman UPD {update}]'
}

# show UPD in colors and count
arch_updates {
    format = '[\?if=pacman [\?if=foreign&color=update UPD'
    format += '|\?color=pacman UPD]|[\?if=foreign&color=foreign '
    format += 'UPD]][\?not_zero  {update}]'
}

# show UPD in mixed colors and count
arch_updates {
    format = '[\?if=pacman [\?if=foreign [\?color=pacman&show U]'
    format += '[\?color=update&show P][\?color=foreign&show D]|\?color=pacman UPD]|'
    format += '[\?if=foreign&color=foreign UPD]][\?not_zero  {update}]'
}

# show separate numbers of updates in seperate colors
arch_updates {
    format = '[\?if=update UPD '
    format += '[\?not_zero&color=pacman {pacman}][\?soft , ]'
    format += '[\?not_zero&color=foreign {foreign}]]'
}

# show PAC, FOR, or UPD in colors and count
arch_updates {
    format = '[\?if=pacman [\?if=foreign&color=update UPD|\?color=pacman PAC]'
    format += '|[\?if=foreign&color=foreign FOR]][\?not_zero  {update}]'
}

# show count and name of updates in seperate colors
arch_updates {
    format = '[\?not_zero UPD {update}: '
    format += '[\?max_length=999 {format_pacman}][\?soft  ]'
    format += '[\?max_length=999 {format_foreign}]]'
    format_pacman = '\?color=pacman {name}'
    format_foreign = '\?color=foreign {name}'
    format_pacman_separator = ' '
    format_foreign_separator = ' '
}

# show update bars, ie \|, or blocks, ie \u25b0
arch_updates {
    format = '[{format_pacman}][{format_foreign}]'
    format_pacman = '\?color=pacman \u25b0'
    format_foreign = '\?color=foreign \u25b0'
}

# show count thresholds
arch_updates {
    format = '[\?not_zero [\?color=update&show UPD] {update}]'
    thresholds = [(0, 'good'), (20, 'degraded'), (30, 'bad')]
}

# reminder: you can replace UPD with an icon
arch_updates {
    format = '\u26ca'  # shogi piece, turned black
}

# reminder: you can mix some things together, eg update shield
# and color threshold, to make a nice indicator - my favorite.
arch_updates {
    format = '[\?not_zero [\?color=update&show \u26ca] {update}]'
    thresholds = [(0, 'good'), (20, 'degraded'), (30, 'bad')]
}

# add your snippets here
arch_updates {
    format = '...'
}
```

SAMPLE OUTPUT
{'full_text': 'UPD 15'}
"""

STRING_ERROR = 'not configured'
STRING_NOT_INSTALLED = 'not installed'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 3600
    format = 'UPD {update}'
    format_foreign = None
    format_foreign_separator = None
    format_pacman = None
    format_pacman_separator = None
    thresholds = []

    class Meta:
        deprecated = {
            'rename_placeholder': [
                {
                    'placeholder': 'aur',
                    'new': 'foreign',
                    'format_strings': ['format'],
                },
                {
                    'placeholder': 'total',
                    'new': 'update',
                    'format_strings': ['format'],
                },
            ],
        }

    def post_config_hook(self):
        if not self.py3.check_commands(['checkupdates']):
            raise Exception(STRING_NOT_INSTALLED)

        self.pacman = self.py3.format_contains(self.format, ['*pacman', 'update'])
        self.foreign = self.py3.check_commands(['cower']) and \
            self.py3.format_contains(self.format, ['*foreign', 'update'])

        if not self.pacman and not self.foreign:
            raise Exception(STRING_ERROR)

        if not self.format_pacman_separator:
            self.format_pacman_separator = ''
        if not self.format_foreign_separator:
            self.format_foreign_separator = ''

    def _get_pacman_updates(self):
        try:
            return self.py3.command_output(['checkupdates'])
        except self.py3.CommandError as ce:
            return ce.output

    def _get_foreign_updates(self):
        try:
            return self.py3.command_output(['cower', '-u'])
        except self.py3.CommandError as ce:
            return ce.output

    def arch_updates(self):
        new_foreign = []
        new_pacman = []
        format_foreign = None
        format_pacman = None
        foreign_data = []
        pacman_data = []

        if self.pacman:
            pacman_data = self._get_pacman_updates().splitlines()
        if self.foreign:
            foreign_data = self._get_foreign_updates().splitlines()

        count_pacman = len(pacman_data)
        count_foreign = len(foreign_data)
        count_update = count_pacman + count_foreign

        if self.format_pacman and pacman_data:
            for line in pacman_data:
                package = line.split()
                new_pacman.append(self.py3.safe_format(
                    self.format_pacman, {
                        'name': package[0],
                        'old_version': package[1],
                        'new_version': package[3],
                    }))

            format_pacman = self.py3.composite_join(self.py3.safe_format(
                self.format_pacman_separator), new_pacman)

        if self.format_foreign and foreign_data:
            for line in foreign_data:
                package = line.split()
                new_foreign.append(self.py3.safe_format(
                    self.format_foreign, {
                        'name': package[1],
                        'old_version': package[2],
                        'new_version': package[4],
                    }))

            format_foreign = self.py3.composite_join(self.py3.safe_format(
                self.format_foreign_separator), new_foreign)

        if self.thresholds:
            self.py3.threshold_get_color(count_update, 'update')
            self.py3.threshold_get_color(count_pacman, 'pacman')
            self.py3.threshold_get_color(count_foreign, 'foreign')

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {
                    'update': count_update,
                    'pacman': count_pacman,
                    'foreign': count_foreign,
                    'format_pacman': format_pacman,
                    'format_foreign': format_foreign,
                })}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
