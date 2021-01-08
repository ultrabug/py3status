r"""
Display information about the currently running emerge process.

Configuration parameters:
    cache_timeout: how often we refresh this module in second.
        NOTE: when emerge is running, we will refresh this module every second.
        (default 30)
    emerge_log_file: path to the emerge log file.
        (default '/var/log/emerge.log')
    format: display format for this module
        *(default '{prefix}[\?if=is_running : [\?if=!total=0 '
        '[{current}/{total} {action} {category}/{pkg}]'
        '|calculating...]|: stopped 0/0]')*
    prefix: prefix in statusbar
        (default "emrg")

Format placeholders:
    {action} current emerge action
    {category} category of the currently emerged package
    {current} number of package that is currently emerged
    {pkg} name of the currently emerged packaged
    {total} total number of packages that will be emerged

Examples:
```
# Hide if not running
emerge_status {
    format = "[\?if=is_running {prefix}: [\?if=!total=0 "
    format += "{current}/{total} {action} {category}/{pkg}"
    format += "|calculating...]]"
}

# Minimalistic
emerge_status {
    format = "[\?if=is_running [\?if=!total=0 {current}/{total}]]"
}

# Minimalistic II
emerge_status {
    format = "[\?if=is_running {current}/{total}]"
}
```

@author AnwariasEu

SAMPLE OUTPUT
{'full_text': 'emrg : 0/0'}
"""

import re
import copy

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 30
    emerge_log_file = "/var/log/emerge.log"
    format = (
        r"{prefix}[\?if=is_running : [\?if=!total=0 [{current}/{total}"
        " {action} {category}/{pkg}]|calculating...]|: stopped 0/0]"
    )
    prefix = "emrg"

    def _emerge_running(self):
        """
        Check if emerge is running.
        Returns true if at least one instance of emerge is running.
        """
        try:
            self.py3.command_output(["pgrep", "emerge"])
            return True
        except Exception:
            return False

    def post_config_hook(self):
        if not self.py3.check_commands("emerge"):
            raise Exception(STRING_NOT_INSTALLED)
        self.ret_default = {
            "action": "",
            "category": "",
            "current": 0,
            "is_running": False,
            "pkg": "",
            "total": 0,
        }

    def _get_progress(self):
        """
        Get current progress of emerge.
        Returns a dict containing current and total value.
        """
        input_data = []
        ret = {}

        # traverse emerge.log from bottom up to get latest information
        last_lines = self.py3.command_output(["tail", "-50", self.emerge_log_file])
        input_data = last_lines.split("\n")
        input_data.reverse()

        for line in input_data:
            if "*** terminating." in line:
                # copy content of ret_default, not only the references
                ret = copy.deepcopy(self.ret_default)
                break
            else:
                status_re = re.compile(
                    r"\((?P<cu>[\d]+) of (?P<t>[\d]+)\) "
                    r"(?P<a>[a-zA-Z/]+( [a-zA-Z]+)?) "
                    r"\((?P<ca>[\w\-]+)/(?P<p>[\w.]+)"
                )
                res = status_re.search(line)
                if res is not None:
                    ret["action"] = res.group("a").lower()
                    ret["category"] = res.group("ca")
                    ret["current"] = res.group("cu")
                    ret["pkg"] = res.group("p")
                    ret["total"] = res.group("t")
                    break
        return ret

    def emerge_status(self):
        """
        """
        response = {}
        ret = copy.deepcopy(self.ret_default)
        if self._emerge_running():
            ret = self._get_progress()
            ret["is_running"] = True
            response["cached_until"] = self.py3.time_in(0)
        else:
            response["cached_until"] = self.py3.time_in(self.cache_timeout)
        response["full_text"] = self.py3.safe_format(self.format, ret)
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
