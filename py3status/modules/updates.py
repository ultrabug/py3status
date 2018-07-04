# -*- coding: utf-8 -*-
"""
Display numbers of updates for various linux distributions.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 600)
    format: display format for this module, otherwise auto (default None)
    thresholds: specify color thresholds to use *(default [(0, 'darkgray'),
        (10, 'degraded'), (20, 'orange'), (30, 'bad')])*

Format placeholders:
    {update}  number of updates, eg 0
    {apk}     number of updates, eg 0 .. Alpine Linux     .. NOT TESTED
    {apt}     number of updates, eg 0 .. Debian, Ubuntu
    {auracle} number of updates, eg 0 .. Arch Linux (AUR)
    {cower}   number of updates, eg 0 .. Arch Linux (AUR)
    {dnf}     number of updates, eg 0 .. Fedora           .. NOT TESTED
    {eopkg}   number of updates, eg 0 .. Solus
    {pacman}  number of updates, eg 0 .. Arch Linux
    {xbps}    number of updates, eg 0 .. Void Linux       .. NOT TESTED
    {yay}     number of updates, eg 0 .. Arch Linux (AUR)
    {zypper}  number of updates, eg 0 .. openSUSE         .. NOT TESTED

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author lasers

Examples:
```
# multiple distributions, same format
updates {
    format = '[\?not_zero Updates [\?color=update {update}]]'
}

# Arch Linux
updates {
    format = 'Updates [\?color=pacman {pacman}]/[\?color=cower {cower}]'
    # format = 'Updates [\?color=pacman {pacman}]/[\?color=auracle {auracle}]'
    # format = 'Updates [\?color=pacman {pacman}]/[\?color=yay {yay}]'
}
```

SAMPLE OUTPUT
[{'full_text': 'Apk '}, {'full_text': '3', 'color': '#a9a9a9'}]

14pkgs
[{'full_text': 'Apt '}, {'full_text': '14', 'color': '#00FF00'}]

29and5pkgs
[{'full_text': 'Pacman '}, {'full_text': '29 ', 'color': '#FFFF00'},
{'full_text': 'Cower '}, {'full_text': '5', 'color': '#a9a9a9'}]

35pkgs
[{'full_text': 'Zypper '}, {'full_text': '34', 'color': '#ffa500'}]

45pkgs
[{'full_text': 'Xbps '}, {'full_text': '45', 'color': '#FF0000'}]

no_updates
{'full_text': 'No Updates'}
"""


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


class Cower(Update):
    def get_output(self):
        try:
            self.parent.py3.command_output(self.command)
            return None
        except self.parent.py3.CommandError as ce:
            return ce.output


class Dnf(Update):
    def count_updates(self, output):
        lines = output.splitlines()[2:]
        return len([x for x in lines if 'Security:' not in x])


class Eopkg(Update):
    def get_output(self):
        output = self.parent.py3.command_output(self.command)
        if "No packages to upgrade." in output:
            return ''
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
    thresholds = [(0, 'darkgray'), (10, 'degraded'),
                  (20, 'orange'), (30, 'bad')]

    class Meta:
        deprecated = {
            "rename_placeholder": [
                {
                    "placeholder": "aur",
                    "new": "cower",
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        managers = [
            ("pacman", ["checkupdates"]),
            ("auracle", ["auracle", "sync"]),
            ("cower", ["cower", "-u"]),
            ("yay", ["yay", "--query", "--upgrades", "--aur"]),
            ("apk", ["apk", "version", "-l", '"<"']),
            ("apt", ["apt", "list", "--upgradeable"]),
            ("dnf", ["dnf", "check-upgrades"]),
            ("eopkg", ["eopkg", "list-upgrades"]),
            ("pkg", ["pkg", "upgrade", "--dry-run", "--quiet"]),
            ("xbps", ["xbps-install", "--update", "--dry-run"]),
            ("zypper", ["zypper", "list-updates"]),
        ]

        managed = getattr(self, 'managers', [])
        if not managed:
            placeholders = self.py3.get_placeholders_list(self.format or '')
            managed = [x for x in placeholders if x != 'update']

        names = []
        self.backends = []
        for name, command in managers:
            if managed:
                for manager in managed:
                    if manager == name:
                        break
                else:
                    continue
            if self.py3.check_commands(command[0]):
                names.append(name)
                try:
                    backend = globals()[name.capitalize()]
                except KeyError:
                    backend = Update
                self.backends.append(backend(self, name, command))

        if not self.format:
            auto = "[\?not_zero {Name} [\?color={name} {{{name}}}]]"
            self.format = "[{}|\?show No Updates]".format("[\?soft  ]".join(
                auto.format(Name=x.capitalize(), name=x) for x in names
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

    module_test(Py3status)
