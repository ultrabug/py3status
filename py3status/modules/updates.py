# -*- coding: utf-8 -*-
"""
Display numbers of updates for various linux distributions.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 600)
    format: display format for this module, otherwise auto (default None)
    managers: specify a list and/or 2-tuples of managers to use (default [])
    thresholds: specify color thresholds to use *(default [(0, 'darkgray'),
        (10, 'degraded'), (20, 'orange'), (30, 'bad')])*

Format placeholders:
    {update}  number of updates, eg 0
    {apk}     number of updates, eg 0 .. Alpine Linux     [NOT TESTED]
    {apt}     number of updates, eg 0 .. Debian, Ubuntu
    {auracle} number of updates, eg 0 .. Arch Linux (AUR)
    {eopkg}   number of updates, eg 0 .. Solus
    {pacman}  number of updates, eg 0 .. Arch Linux
    {pikaur}  number of updates, eg 0 .. Arch Linux (AUR)
    {xbps}    number of updates, eg 0 .. Void Linux       [NOT TESTED]
    {yay}     number of updates, eg 0 .. Arch Linux (AUR)
    {zypper}  number of updates, eg 0 .. openSUSE         [NOT TESTED]

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author Iain Tatch <iain.tatch@gmail.com> (arch)
@author Joshua Pratt <jp10010101010000@gmail.com> (apt)
@author lasers (apk, auracle, eopkg, pikaur, xbps, yay, zypper)
@license BSD (apt, arch)

Examples:
```
# multiple distributions, same format
updates {
    format = '[\?not_zero UPD [\?color=update {update}]]'
}

# Arch Linux
updates {
    format = 'UPD [\?color=pacman {pacman}]/[\?color=auracle {auracle}]'
    # format = 'UPD [\?color=pacman {pacman}]/[\?color=pikaur {pikaur}]'
    # format = 'UPD [\?color=pacman {pacman}]/[\?color=yay {yay}]'
}

# specify a list of managers (aka supported placeholders)
updates {
    managers = ['pacman', 'yay']
    # Similar to 'Pacman {pacman} Yay {yay}'
}

# specify a list of 2-tuples managers (aka custom commands)
updates {
    managers = [('PAC', 'checkupdates'), ('AUR', 'auracle sync')]
    # Similar to 'PAC {pac} AUR {aur}'
}

# specify a list of managers and/or 2-tuples (aka mixed options)
updates {
    managers = ['pacman', ('AUR', 'auracle sync')]
    # Similiar to 'Pacman {pacman} AUR {aur}'
}
```

SAMPLE OUTPUT
[{'full_text': 'Apk '}, {'full_text': '3', 'color': '#a9a9a9'}]

14pkgs
[{'full_text': 'Apt '}, {'full_text': '14', 'color': '#00FF00'}]

29and5pkgs
[{'full_text': 'Pacman '}, {'full_text': '29 ', 'color': '#FFFF00'},
{'full_text': 'Auracle '}, {'full_text': '5', 'color': '#a9a9a9'}]

35pkgs
[{'full_text': 'Zypper '}, {'full_text': '34', 'color': '#ffa500'}]

45pkgs
[{'full_text': 'Xbps '}, {'full_text': '45', 'color': '#FF0000'}]
"""

STRING_INVALID_MANAGERS = 'invalid managers'


class Update:
    def __init__(self, parent, name, command):
        self.parent = parent
        self.name = name
        self.command = command

    def get_output(self):
        try:
            return self.parent.py3.command_output(self.command)
        except self.parent.py3.CommandError:
            return None

    def count_updates(self, output):
        return len(output.splitlines())

    def get_updates(self):
        output = self.get_output()
        if output is None:
            return {self.name: output}
        return {self.name: self.count_updates(output)}


class Apt(Update):
    def count_updates(self, output):
        return len(output.splitlines()[1:])


class Apk(Update):
    def count_updates(self, output):
        return len(output.splitlines()[1:])


class Eopkg(Update):
    def get_output(self):
        output = self.parent.py3.command_output(self.command)
        if "No packages to upgrade." in output:
            return ""
        return output


class Zypper(Update):
    def count_updates(self, output):
        return len([x for x in output.splitlines() if x][4:])


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 600
    format = None
    managers = []
    thresholds = [
        (0, 'darkgray'), (10, 'degraded'), (20, 'orange'), (30, 'bad')]

    class Meta:
        deprecated = {
            "rename_placeholder": [
                {
                    "placeholder": "aur",
                    "new": "auracle",
                    "format_strings": ["format"],
                },
                {
                    "placeholder": "total",
                    "new": "update",
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        managers = [
            ("Pacman", "checkupdates"),
            ("Auracle", "auracle sync --color=never"),
            ("Yay", "yay --query --upgrades --aur"),
            ("Pikaur", "pikaur -Quaq"),
            ("Apk", "apk version -l '<'"),
            ("Apt", "apt list --upgradeable"),
            ("Eopkg", "eopkg list-upgrades"),
            ("Pkg", "pkg upgrade --dry-run --quiet"),
            ("Xbps", "xbps-install --update --dry-run"),
            ("Zypper", "zypper list-updates"),
        ]

        if self.managers:
            new_managers = []
            for entry in self.managers:
                if isinstance(entry, tuple):
                    if len(entry) != 2 or entry[0].lower() == 'update':
                        raise Exception(STRING_INVALID_MANAGERS)
                    new_managers.append(entry)
                else:
                    name = entry.lower()
                    if name == 'update':
                        raise Exception(STRING_INVALID_MANAGERS)
                    for manager in managers:
                        if manager[0].lower() == name:
                            new_managers.append(manager)
                            break
            managers = new_managers

        placeholders = self.py3.get_placeholders_list(self.format or '')
        placeholders = [x for x in placeholders if x != 'update']

        formats = []
        self.backends = []
        for name, command in managers:
            name_lowercased = name.lower()
            if placeholders and name_lowercased not in placeholders:
                continue
            if self.py3.check_commands(command.split()[0]):
                try:
                    backend = globals()[name.capitalize()]
                except KeyError:
                    backend = Update
                formats.append((name, name_lowercased))
                self.backends.append(backend(self, name_lowercased, command))

        if not self.format:
            if getattr(self, 'verbose', False):
                if getattr(self, 'not_zero', False):
                    auto = "[\?not_zero {name} [\?color={lower} {{{lower}}}]]"
                else:
                    auto = "[{name} [\?color={lower} {{{lower}}}]]"
                format_string = "{}"
                separator = "[\?soft  ]"
            else:
                if getattr(self, 'not_zero', False):
                    auto = "[\?not_zero [\?color={lower} {{{lower}}}]]"
                else:
                    auto = "[\?color={lower} {{{lower}}}]"
                format_string = "[\?if=update UPD {}]"
                separator = "[\?soft /]"
            self.format = format_string.format(separator.join(
                auto.format(name=n, lower=l) for n, l in formats
            ))

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def updates(self):
        update_data = {'update': 0}
        for backend in self.backends:
            update = backend.get_updates()
            update_data['update'] += update[backend.name] or 0
            update_data.update(update)

        for x in self.thresholds_init:
            if x in update_data:
                self.py3.threshold_get_color(update_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, update_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status, config={'verbose': True})
