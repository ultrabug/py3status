"""
Display number of pending updates for Arch Linux.

Configuration parameters:
    format: display format for this module, otherwise auto (default None)
    hide_if_zero: don't show on bar if True (default False)
    pacman_log_location: location of the pacman log (default '/var/log/pacman.log')
    refresh_interval: interval (in seconds) between refreshing data from package
        database or AUR. Note that this module may refresh sooner than the
        specified interval, if pacman log is modified since the last refresh
        time. (default 3600)

Format placeholders:
    {aur} Number of pending aur updates
    {pacman} Number of pending pacman updates
    {total} Total updates pending

Requires:
    pacman-contrib: contributed scripts and tools for pacman systems
    auracle: a flexible command line client for arch linux's user repository
    trizen: lightweight pacman wrapper and AUR helper
    yay: yet another yogurt. pacman wrapper and aur helper written in go
    paru: feature packed AUR helper
    pikaur: pacman wrapper and AUR helper written in python

@author Iain Tatch <iain.tatch@gmail.com>
@license BSD

SAMPLE OUTPUT
{'full_text': 'UPD: 5'}

aur
{'full_text': 'UPD: 15/4'}
"""
import os
import time

STRING_NOT_INSTALLED = "{} not installed"
CACHE_KEY_PACMAN = "arch_updates_pacman_count"
CACHE_KEY_AUR = "arch_updates_aur_count"
CACHE_KEY_TIMESTAMP = "arch_updates_timestamp"


class Py3status:
    """ """

    # available configuration parameters
    format = None
    hide_if_zero = False
    pacman_log_location = "/var/log/pacman.log"
    refresh_interval = 3600

    class Meta:
        deprecated = {
            "remove": [{"param": "include_aur", "msg": "obsolete"}],
            "rename": [
                {
                    "param": "cache_timeout",
                    "new": "refresh_interval",
                    "msg": "cache_timeout has been renamed to refresh_interval",
                }
            ],
        }

    def post_config_hook(self):
        helper = {
            "pacman": self.py3.check_commands(["checkupdates"]),
            "aur": self.py3.check_commands(["auracle", "trizen", "yay", "paru", "pikaur"]),
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
        except self.py3.CommandError as ce:
            # yay returns 1 if there are no updates.
            return 0 if ce.error_code == 1 else None

    def _get_paru_updates(self):
        try:
            updates = self.py3.command_output(["paru", "-Qua"])
            return len(updates.splitlines())
        except self.py3.CommandError as ce:
            return None if ce.error else 0

    def _get_pikaur_updates(self):
        try:
            updates = self.py3.command_output(["pikaur", "-Qua"])
            return len(updates.splitlines())
        except self.py3.CommandError as ce:
            return None if ce.error else 0

    def arch_updates(self):
        counts = self._get_cached_value()
        if counts is None:
            counts = self._get_package_counts()

            self.py3.storage_set(CACHE_KEY_PACMAN, counts[0])
            self.py3.storage_set(CACHE_KEY_AUR, counts[1])
            self.py3.storage_set(CACHE_KEY_TIMESTAMP, time.time())

        return {"full_text": self._format_display_text(*counts)}

    def _get_cached_value(self):
        pacman = self.py3.storage_get(CACHE_KEY_PACMAN)
        aur = self.py3.storage_get(CACHE_KEY_AUR)
        generated_at = self.py3.storage_get(CACHE_KEY_TIMESTAMP)

        if pacman is None or aur is None or generated_at is None:
            return None

        # If the log file has been updated since last refresh, the update number
        # is likely no longer valid. We skip the cache here.
        log_mtime = os.path.getmtime(self.pacman_log_location)
        if generated_at < log_mtime:
            return None

        if generated_at + self.refresh_interval > time.time():
            return pacman, aur

        return None

    def _get_package_counts(self):
        pacman, aur = None, None
        if self._get_pacman_updates:
            pacman = self._get_pacman_updates() or 0
        if self._get_aur_updates:
            aur = self._get_aur_updates() or 0

        return pacman, aur

    def _format_display_text(self, pacman, aur):
        total = pacman + aur
        if self.hide_if_zero and not total:
            return ""

        arch_data = {"aur": aur, "pacman": pacman, "total": total}
        return self.py3.safe_format(self.format, arch_data)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
