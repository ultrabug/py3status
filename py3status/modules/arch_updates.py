# -*- coding: utf-8 -*-
"""
Display number of pending updates for Arch Linux.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 600)
    format: display format for this module, see Examples below (default None)
    hide_if_zero: Don't show on bar if True (default False)
    include_aur: Check for AUR updates with auracle or yay (default False)

Format placeholders:
    {aur} Number of pending aur updates
    {pacman} Number of pending pacman updates
    {total} Total updates pending

Requires:
    pacman-contrib: contributed scripts and tools for pacman systems
    auracle: a flexible command line client for arch linux's user repository
    yay: yet another yogurt. pacman wrapper and aur helper written in go

Examples:
```
# default formats
arch_updates {
    format = 'UPD: {pacman}'        # if include_aur is False
    format = 'UPD: {pacman}/{aur}'  # if include_aur is True
}
```

@author Iain Tatch <iain.tatch@gmail.com>
@license BSD

SAMPLE OUTPUT
{'full_text': 'UPD: 5'}

arch_updates_aur
{'full_text': 'UPD: 15/4'}
"""

FORMAT_PACMAN_ONLY = "UPD: {pacman}"
FORMAT_PACMAN_AND_AUR = "UPD: {pacman}/{aur}"
STRING_NOT_INSTALLED = "{} not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 600
    format = None
    hide_if_zero = False
    include_aur = False

    def post_config_hook(self):
        if not self.format:
            if not self.include_aur:
                self.format = FORMAT_PACMAN_ONLY
            else:
                self.format = FORMAT_PACMAN_AND_AUR
        self.include_aur = self.py3.format_contains(self.format, "aur")
        self.include_pacman = self.py3.format_contains(self.format, "pacman")
        if self.py3.format_contains(self.format, "total"):
            self.include_aur = True
            self.include_pacman = True

        if self.include_aur:
            aurs = ["auracle", "yay", "cower"]
            command = self.py3.check_commands(aurs)
            if command:
                self._check_aur_updates = getattr(
                    self, "_check_aur_updates_{}".format(command)
                )
            else:
                self.include_aur = False
                self.py3.notify_user(STRING_NOT_INSTALLED.format(", ".join(aurs)))

    def arch_updates(self):
        pacman_updates = aur_updates = total = None

        if self.include_pacman:
            pacman_updates = self._check_pacman_updates()

        if self.include_aur:
            aur_updates = self._check_aur_updates()

        if pacman_updates is not None or aur_updates is not None:
            total = (pacman_updates or 0) + (aur_updates or 0)

        if self.hide_if_zero and total == 0:
            full_text = ""
        else:
            full_text = self.py3.safe_format(
                self.format,
                {"aur": aur_updates, "pacman": pacman_updates, "total": total},
            )
        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }

    def _check_pacman_updates(self):
        try:
            updates = self.py3.command_output(["checkupdates"])
            return len(updates.splitlines())
        except self.py3.CommandError:
            return None

    def _check_aur_updates_auracle(self):
        try:
            updates = self.py3.command_output(["auracle", "sync"])
            return len(updates.splitlines())
        except self.py3.CommandError:
            return None

    def _check_aur_updates_cower(self):
        try:
            self.py3.command_output(["cower", "-u"])
        except self.py3.CommandError as ce:
            return len(ce.output.splitlines())
        return None

    def _check_aur_updates_yay(self):
        try:
            updates = self.py3.command_output(["yay", "-Qua"])
            return len(updates.splitlines())
        except self.py3.CommandError:
            return None


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
