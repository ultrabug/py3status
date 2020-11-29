"""
Display number of pending updates for Arch Linux.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 600)
    format: display format for this module, otherwise auto (default None)
    hide_if_zero: don't show on bar if True (default False)

Format placeholders:
    {aur} Number of pending aur updates
    {pacman} Number of pending pacman updates
    {total} Total updates pending

Requires:
    pacman-contrib: contributed scripts and tools for pacman systems
    auracle: a flexible command line client for arch linux's user repository
    trizen: lightweight pacman wrapper and AUR helper
    yay: yet another yogurt. pacman wrapper and aur helper written in go
```

@author Iain Tatch <iain.tatch@gmail.com>
@license BSD

SAMPLE OUTPUT
{'full_text': 'UPD: 5'}

aur
{'full_text': 'UPD: 15/4'}
"""

STRING_NOT_INSTALLED = "{} not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 600
    format = None
    hide_if_zero = False

    class Meta:
        deprecated = {"remove": [{"param": "include_aur", "msg": "obsolete"}]}

    def post_config_hook(self):
        helper = {
            "pacman": self.py3.check_commands(["checkupdates"]),
            "aur": self.py3.check_commands(["auracle", "trizen", "yay", "cower"]),
        }
        if self.format:
            placeholders = self.py3.get_placeholders_list(self.format)
            if "total" in placeholders:
                pass
            elif not any(helper.values()):
                raise Exception(STRING_NOT_INSTALLED.format("pacman, aur"))
            else:
                for name in helper:
                    if name not in placeholders:
                        helper[name] = None
                    elif not helper[name]:
                        raise Exception(STRING_NOT_INSTALLED.format(name))
        elif all(helper.values()):
            self.format = "UPD: {pacman}/{aur}"
        elif helper["pacman"]:
            self.format = "UPD: {pacman}"
        elif helper["aur"]:
            self.format = "UPD: ?/{aur}"
        else:
            raise Exception(STRING_NOT_INSTALLED.format("pacman, aur"))

        for key in helper:
            value = getattr(self, "_get_{}_updates".format(helper[key]), None)
            setattr(self, f"_get_{key}_updates", value)

    def _get_checkupdates_updates(self):
        try:
            updates = self.py3.command_output(["checkupdates"])
            return len(updates.splitlines())
        except self.py3.CommandError as ce:
            return None if ce.error else 0

    def _get_auracle_updates(self):
        try:
            updates = self.py3.command_output(["auracle", "sync"])
            return len(updates.splitlines())
        except self.py3.CommandError as ce:
            return None if ce.error else 0

    def _get_cower_updates(self):
        try:
            self.py3.command_output(["cower", "-u"])
            return None
        except self.py3.CommandError as ce:
            return len(ce.output.splitlines())

    def _get_trizen_updates(self):
        try:
            updates = self.py3.command_output(["trizen", "-Suaq"])
            return len(updates.splitlines())
        except self.py3.CommandError:
            return None

    def _get_yay_updates(self):
        try:
            updates = self.py3.command_output(["yay", "-Qua"])
            return len(updates.splitlines())
        except self.py3.CommandError:
            return None

    def arch_updates(self):
        pacman, aur, total, full_text = None, None, None, ""

        if self._get_pacman_updates:
            pacman = self._get_pacman_updates()
        if self._get_aur_updates:
            aur = self._get_aur_updates()
        if pacman is not None or aur is not None:
            total = (pacman or 0) + (aur or 0)

        if not (self.hide_if_zero and not total):
            arch_data = {"aur": aur, "pacman": pacman, "total": total}
            full_text = self.py3.safe_format(self.format, arch_data)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
