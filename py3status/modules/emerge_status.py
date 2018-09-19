# -*- coding: utf-8 -*-
"""
Emerge_status provides a short information on the current
emerge status if there is an emerge process currently running

Configuration parameters:
    cache_timeout: how often we refresh this module in second (default 0)
    format: *(default '{prefix} [\\?if=is_running [\\?if=!total=0 [{current}/{total}'
              ' {action} {category}/{pkg}]| calculating...]| stopped 0/0]')*
    prefix: prefix in statusbar (default "EMRG: ")

Format placeholders:
    {current} Number of package that is currently emerged
    {total} Total number of packages that will be emerged
    {category} Category of the currently emerged package
    {pkg} Name of the currently emerged packaged
    {action} Current emerge action

Examples:
```
# Hide if not running
emerge_status {
    format = ('[\?if=is_running {prefix} [\?if=!total=0 {current}/{total} '
              '{action} {category}/{pkg}]]')
}
# Minimalistic
emerge_status {
    format = ('[\?if=is_running [\?if=!total=0 {current}/{total}]]')
}

# Minimalistic II
emerge_status {
    format = ('[\?if=is_running {current}/{total}]')
}

# Hide if not running
emerge_status {
    format = ('[\?if=is_running {prefix} [\?if=!total=0 {current}/{total} '
              '{action} {category}/{pkg}]| calculating...]')
}
```


@author AnwariasEu
"""

import re
import copy

STRING_NOT_INSTALLED = 'not installed'


class Py3status:
    """
    """
    cache_timeout = 0
    format = ('{prefix} [\?if=is_running [\?if=!total=0 [{current}/{total}'
              ' {action} {category}/{pkg}]| calculating...]| stopped 0/0]')

    prefix = "EMRG: "

    def _emerge_running(self):
        """
        Check if emerge is running.
        Returns true if at least one instance of emerge is running.
        """
        try:
            self.py3.command_output(['pgrep', 'emerge'])
            return True
        except Exception:
            return False

    def post_config_hook(self):
        if not self.py3.check_commands('emerge'):
            raise Exception(STRING_NOT_INSTALLED)
        self.ret_default = {
            'current': 0,
            'total': 0,
            'category': "",
            'pkg': "",
            'action': "",
            'is_running': False}

    def _get_progress(self):
        """
        Get current progress of emerge.

        returns a dict containing current and total value.
        """
        emerge_log_file = '/var/log/emerge.log'

        ret = {}

        input_data = []

        """
        Open file, if unable to open it py3status catches the error.
        No need for explizit error handling here.
        """
        with open(emerge_log_file, 'r') as fp:
            input_data = fp.readlines()

        """
        Traverse emerge.log from bottom up to get latest information
        """

        input_data.reverse()

        for line in input_data:
            if "*** terminating." in line:
                # Copy content of ret_default, not only the references
                ret = copy.deepcopy(self.ret_default)
                break
            else:
                status_re = re.compile(
                    "\((?P<cu>[\d]+) of (?P<t>[\d]+)\) "
                    "(?P<a>[a-zA-Z\/]+( [a-zA-Z]+)?) "
                    "\((?P<ca>[\w\-]+)\/(?P<p>[\w\.]+)"
                )
                res = status_re.search(line)
                if res is not None:
                    ret['current'] = res.group('cu')
                    ret['total'] = res.group('t')
                    ret['category'] = res.group('ca')
                    ret['pkg'] = res.group('p')
                    ret['action'] = res.group('a')
                    break
        return ret

    def emerge_status(self):
        """
        Emerge Status main routine
        """
        response = {}
        response['cached_until'] = self.py3.time_in(self.cache_timeout)
        ret = copy.deepcopy(self.ret_default)
        if self._emerge_running():
            ret = self._get_progress()
            ret['is_running'] = True
        response['full_text'] = self.py3.safe_format(self.format, ret)
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        'show_pkg': False,
        'hide_if_stopped': True
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
