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
    {dnf}     number of updates, eg 0 .. Fedora
    {eopkg}   number of updates, eg 0 .. Solus
    {flatpak} number of updates, eg 0 .. Flatpak
    {pacman}  number of updates, eg 0 .. Arch Linux
    {pakku}   number of updates, eg 0 .. Arch Linux (AUR)
    {pikaur}  number of updates, eg 0 .. Arch Linux (AUR)
    {pkg}     number of updates, eg 0 .. FreeBSD          [NOT TESTED]
    {snappy}  number of updates, eg 0 .. Snappy
    {trizen}  number of updates, eg 0 .. Arch Linux (AUR)
    {xbps}    number of updates, eg 0 .. Void Linux       [NOT TESTED]
    {yay}     number of updates, eg 0 .. Arch Linux (AUR)
    {zypper}  number of updates, eg 0 .. openSUSE         [NOT TESTED]

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

@author Iain Tatch <iain.tatch@gmail.com> (arch)
@author Joshua Pratt <jp10010101010000@gmail.com> (apt)
@author lasers (apk, auracle, eopkg, flatpak, pakku, pikaur, pkg, snappy, trizen, xbps, yay, zypper)
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


class Dnf(Update):
    def count_updates(self, output):
        return len(output.splitlines()[1:])


class Eopkg(Update):
    def get_output(self):
        output = self.parent.py3.command_output(self.command)
        if "No packages to upgrade." in output:
            return ""
        return output


class Pakku(Update):
    def get_output(self):
        try:
            return self.parent.py3.command_output(self.command)
        except self.parent.py3.CommandError as ce:
            return ce.output

    def count_updates(self, output):
        return len([x for x in output.splitlines() if x == "aur"])


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
        (0, "darkgray"),
        (10, "degraded"),
        (20, "orange"),
        (30, "bad"),
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
        with open("/etc/os-release") as f:
            multiple = "archlinux" in f.read()
            if multiple:
                managers = [
                    ("Pacman", "checkupdates"),  # must be first
                    ("Auracle", "auracle sync -q --color=never"),
                    ("Pakku", "pakku -Suq --print-format '%r' --color=never"),
                    ("Pikaur", "pikaur -Quaq --color=never"),
                    ("Trizen", "trizen -Quaq --color=never"),
                    ("Yay", "yay -Quaq --color=never"),
                ]
            else:
                managers = [
                    ("Apk", "apk version -l '<'"),
                    (
                        "Apt",
                        "apt-get dist-upgrade --dry-run -qq "
                        "-o APT::Get::Show-User-Simulation-Note=no",
                    ),
                    ("Dnf", "dnf list --refresh --upgrades --quiet"),
                    ("Eopkg", "eopkg list-upgrades"),
                    ("Pkg", "pkg upgrade --dry-run --quiet"),
                    ("Xbps", "xbps-install --update --dry-run"),
                    ("Zypper", "zypper list-updates"),
                ]
            managers += [
                ("Flatpak", "flatpak remote-ls --updates --all"),
                ("Snappy", "snap refresh --list --color=never"),
            ]

        if self.managers:
            new_managers = []
            for entry in self.managers:
                if isinstance(entry, tuple):
                    if len(entry) != 2 or entry[0].lower() == "update":
                        raise Exception(STRING_INVALID_MANAGERS)
                    new_managers.append(entry)
                else:
                    name = entry.lower()
                    if name == "update":
                        raise Exception(STRING_INVALID_MANAGERS)
                    for manager in managers:
                        if manager[0].lower() == name:
                            new_managers.append(manager)
                            break
            managers = new_managers

        if self.format:
            placeholders = self.py3.get_placeholders_list(self.format)
            placeholders = [x for x in placeholders if x != "update"]
        else:
            placeholders = []

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
                if not multiple:
                    break

        if not self.format:
            if getattr(self, "verbose", False):
                if getattr(self, "not_zero", False):
                    auto = "[\?not_zero {name} [\?color={lower} {{{lower}}}]]"
                else:
                    auto = "[{name} [\?color={lower} {{{lower}}}]]"
                format_string = "{}"
                separator = "[\?soft  ]"
            else:
                if getattr(self, "not_zero", False):
                    auto = "[\?not_zero [\?color={lower} {{{lower}}}]]"
                else:
                    auto = "[\?color={lower} {{{lower}}}]"
                format_string = "[\?if=update UPD {}]"
                separator = "[\?soft /]"
            self.format = format_string.format(
                separator.join(
                    auto.format(name=n, lower=l) for n, l in formats
                )
            )

        self.thresholds_init = self.py3.get_color_names_list(self.format)

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

    module_test(Py3status, config={"verbose": True})
