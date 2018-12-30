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
    {update}   number of updates, eg 0
    {apk}      number of updates, eg 0 .. Alpine Linux     [NOT TESTED]
    {apt}      number of updates, eg 0 .. Debian, Ubuntu
    {auracle}  number of updates, eg 0 .. Arch Linux (AUR)
    {cargo}    number of updates, eg 0 .. Rust package manager [NOT TESTED]
    {cpan}     number of updates, eg 0 .. CPAN modules (Perl)
    {dnf}      number of updates, eg 0 .. Fedora
    {eopkg}    number of updates, eg 0 .. Solus
    {flatpak}  number of updates, eg 0 .. Flatpak
    {gem}      number of updates, eg 0 .. Ruby Programs and Libaries
    {luarocks} number of updates, eg 0 .. Lua Package Manager
    {npm}      number of updates, eg 0 .. Node.js Package Manager (JavaScript)
    {pacman}   number of updates, eg 0 .. Arch Linux
    {pakku}    number of updates, eg 0 .. Arch Linux (AUR)
    {pikaur}   number of updates, eg 0 .. Arch Linux (AUR)
    {pip}      number of updates, eg 0 .. Pip Installs Packages (Python)
    {pkcon}    number of updates, eg 0 .. PackageKit
    {pkg}      number of updates, eg 0 .. FreeBSD          [NOT TESTED]
    {snappy}   number of updates, eg 0 .. Snappy
    {trizen}   number of updates, eg 0 .. Arch Linux (AUR)
    {xbps}     number of updates, eg 0 .. Void Linux       [NOT TESTED]
    {yay}      number of updates, eg 0 .. Arch Linux (AUR)
    {zypper}   number of updates, eg 0 .. openSUSE         [NOT TESTED]

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author Iain Tatch <iain.tatch@gmail.com> (arch)
@author Joshua Pratt <jp10010101010000@gmail.com> (apt)
@author lasers (apk, auracle, cargo, cpan, eopkg, flatpak, gem, luarocks, npm, pakku, pikaur, pip, pkcon pkg, snappy, trizen, xbps, yay, zypper)
@author tobes (dnf)
@license BSD (apt, arch, dnf)

Examples:
```
# show total updates
updates {
    # total
    format = "UPD [\?color=update {update}]"

    # single managers (eg apt, xbps, etc) would be same as total.
    format = "UPD [\?color=apt {apt}]"

    # archlinux have several aur helpers. querying more than one would give
    # a wrong total so users should keep only one or to specify managers.
    format = "UPD [\?color=update {update}]"
    managers = ['pacman', 'yay']
}

# specify a list and/or 2-tuples of managers
updates {
    # supported placeholders            # UPD {pacman}/{yay}
    managers = ['pacman', 'yay']

    # custom/mixed commands             # UPD {pacman}/{aur}/{custom}
    managers = [
        'pacman',
        ('aur', 'auracle sync'),
        ('custom', 'command querying a list of updates'),
    ]
}
```

SAMPLE OUTPUT
[{'full_text': 'UPD '}, {'full_text': '8', 'color': '#a9a9a9'}]

degraded
[{'full_text': 'UPD '}, {'full_text': '15', 'color': '#ffff00'}]

orange
[{'full_text': 'UPD '}, {'full_text': '34', 'color': '#ffa500'}]

bad
[{'full_text': 'UPD '}, {'full_text': '45', 'color': '#ff0000'}]

arch
[{'full_text': 'UPD '}, {'full_text': '14', 'color': '#ffff00'},
{'full_text': '/'}, {'full_text': '2', 'color': '#a9a9a9'}]
"""

STRING_INVALID_MANAGERS = "invalid managers"
STRING_UNKNOWN_LINUX_DISTRIBUTION = "unknown linux distribution"


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
        return len([x for x in output.splitlines() if x[:4] == "Inst"])


class Apk(Update):
    def count_updates(self, output):
        return len(output.splitlines()[1:])


class Cargo(Update):
    def count_updates(self, output):
        return len(output.splitlines()[2:])


class Dnf(Update):
    def count_updates(self, output):
        return len(output.splitlines()[1:])


class Eopkg(Update):
    def get_output(self):
        output = self.parent.py3.command_output(self.command)
        if "No packages to upgrade." in output:
            return ""
        return output


class Npm(Update):
    def count_updates(self, output):
        return len(output.splitlines()[1:])


class Pakku(Update):
    def get_output(self):
        try:
            return self.parent.py3.command_output(self.command)
        except self.parent.py3.CommandError as ce:
            return ce.output

    def count_updates(self, output):
        return len([x for x in output.splitlines() if x == "aur"])


class Pip(Update):
    def count_updates(self, output):
        return len(output.splitlines()[2:])


class Pkcon(Update):
    def get_output(self):
        try:
            output = self.parent.py3.command_output(self.command)
        except self.parent.py3.CommandError:
            return ""
        return output.partition("Results:\n")[-1]


class Trizen(Update):
    def get_output(self):
        try:
            return self.parent.py3.command_output(self.command)
        except self.parent.py3.CommandError as ce:
            return ce.output


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
        (0, "darkgray"), (10, "degraded"), (20, "orange"), (30, "bad"),
    ]

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
                },
                {
                    "placeholder": "updates",
                    "new": "update",
                    "format_strings": ["format"],
                },
            ]
        }

    def post_config_hook(self):
        distributions = {
            'archlinux': [
                ("Pacman", "checkupdates"),  # must be first
                ("Auracle", "auracle sync -q --color=never"),
                ("Pakku", "pakku -Suq --print-format '%r' --color=never"),
                ("Pikaur", "pikaur -Quaq --color=never"),
                ("Trizen", "trizen -Quaq --color=never"),
                ("Yay", "yay -Quaq --color=never"),
            ],
            'alpine': [("Apk", "apk version -l '<'")],
            'debian': [(
                "Apt", "apt-get dist-upgrade --dry-run -qq "
                "-o APT::Get::Show-User-Simulation-Note=no",
            )],
            'fedora': [("Dnf", "dnf list --refresh --upgrades --quiet")],
            'opensuse': [("Zypper", "zypper list-updates")],
            'solus': [("Eopkg", "eopkg list-upgrades --no-color")],
            'freebsd': [("Pkg", "pkg upgrade --dry-run --quiet")],
            'voidlinux': [("Xbps", "xbps-install --update --dry-run")]
        }
        others = [
            ("Cargo", "cargo outdated --color=never"),
            ("Cpan", "cpan-outdated"),
            ("Flatpak", "flatpak remote-ls --updates --all"),
            ("Gem", "gem outdated --quiet"),
            ("LuaRocks", "luarocks list --outdated --porcelain"),
            ("Npm", "npm outdated"),
            ("Pip", "pip list --outdated --no-color"),
            ("Pkcon", "pkcon get-updates --plain"),
            ("Snappy", "snap refresh --list --color=never"),
        ]

        with open("/etc/os-release") as f:
            release = f.read()
            multiple = "archlinux" in release
            for name in distributions:
                if name in release:
                    managers = distributions[name]
                    break
            else:
                raise Exception(STRING_UNKNOWN_LINUX_DISTRIBUTION)

        log = ""
        custom = []
        self.names = []
        self.backends = []

        if self.format:
            placeholders = self.py3.get_placeholders_list(self.format)
            placeholders = [x for x in placeholders if x != "update"]
        else:
            placeholders = []

        if self.managers:
            for entry in self.managers:
                if isinstance(entry, tuple):
                    if len(entry) != 2 or entry[0].lower() == "update":
                        raise Exception(STRING_INVALID_MANAGERS)
                    custom.append(entry)
                else:
                    name = entry.lower()
                    if name == "update":
                        raise Exception(STRING_INVALID_MANAGERS)
                    for supported in managers + others:
                        if supported[0].lower() == name:
                            custom.append(supported)
                            break
            managers = custom

        if placeholders:
            log += '== Placeholders: '.format(", ".join(placeholders))
        if custom:
            log += '== Custom Managers\n{}'.format(''.join(
                ["- {:10}{}\n".format(*x) for x in custom])
            )
        else:
            log += '== Supported Managers\n{}'.format(''.join(
                ["- {:10}{}\n".format(*x) for x in managers])
            )

        self._init_managers([], custom, placeholders, False)
        self._init_managers(custom, managers, placeholders, multiple)
        if not custom:
            self._init_managers(custom, others, placeholders, True)

        if not self.format:
            auto = "[\?not_zero {name} [\?color={lower} {{{lower}}}]]"
            self.format = "[\?soft  ]".join(
                auto.format(name=x, lower=x.lower()) for x in self.names
            )
        self.thresholds_init = self.py3.get_color_names_list(self.format)

        log += '== Running Managers\n{}'.format(''.join(
            ["- {}\n".format(x) for x in self.names])
        )[:-1]
        self.py3.log(log)

    def _init_managers(self, custom, managers, placeholders, multiple):
        for name, command in managers:
            name_lowercased = name.lower()
            if placeholders and name_lowercased not in placeholders:
                continue
            if any([name_lowercased in x.lower() for x in self.names]):
                continue
            check_command = command.split()[0]
            if check_command == 'cargo':
                check_command = 'cargo-outdated'
            if self.py3.check_commands(check_command):
                try:
                    backend = globals()[name.capitalize()]
                except KeyError:
                    backend = Update
                self.names.append(name)
                self.backends.append(
                    backend(self, name_lowercased, command)
                )
                if not multiple:
                    break

    def updates(self):
        update_data = {"update": 0}
        for backend in self.backends:
            update = backend.get_updates()
            update_data["update"] += update[backend.name] or 0
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

    config = {}
    # config = {'managers': ['pkcon', 'yay', 'pacman']}
    # config = {'format': '{yay}'}

    # config = {
    #     'managers': ['pkcon', 'yay', 'pacman'],
    #     'format': '{yay}',
    # }

    # config = {'managers': ['pkcon']}

    # config = {'managers': ['pkcon', 'yay', 'pacman']}

    # config = {
    #     'managers': ['pkcon', 'yay', 'pacman', 'gem', 'pikaur'],
    #     'format': '{pkcon}'
    # }

    module_test(Py3status, config=config)
