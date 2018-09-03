# -*- coding: utf-8 -*-
"""
Emerge_status provides a short information on the current
emerge status if there is an emerge process currently running

Configuration parameters:
    cache_timeout: how often we refresh this module in second (default 0)
    format: *(default '[[\\?if=!hide_if_stopped {prefix}]|'
                     '[\\?if=is_running {prefix}]]'
                     '[[\\?if=is_running [\\?if=!total=0 {current}/{total}'
                     '[\\?if=show_action {action} ]'
                     '[\\?if=show_pkg {category}/{pkg}]]]|'
                     '[\\?if=!hide_if_stopped 0/0]]')*
    hide_if_stopped: Hide all information if no emerge is running (default False)
    prefix: prefix in statusbar (default "EMRG: ")
    show_action: En/Disable showing action (default True)
    show_pkg: Dis-/Enable showing category and pkg name (default True)

Format placeholders:
    {current} Number of package that is currently emerged
    {total} Total number of packages that will be emerged
    {category} Category of the currently emerged package
    {pkg} Name of the currently emerged packaged
    {action} Current emerge action

Examples:
```
emerge_status {
    hide_if_stopped = True
    prefix = emerge
    show_action = False
    show_pkg = False
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
    format = (
        # show prefix if either show_stopped or if emerge is running
        '[[\?if=!hide_if_stopped {prefix}]|[\?if=is_running {prefix}]]'
        # if emerge is running and total != 0 show
        '[[\?if=is_running [\?if=!total=0 {current}/{total}'
        # show action and cat/pkg only if user wants it
        '[\?if=show_action {action} ][\?if=show_pkg {category}/{pkg}]]]|'
        # if no emerge is running but show_stopped is set show 0/0
        '[\?if=!hide_if_stopped 0/0]]')
    hide_if_stopped = False
    prefix = "EMRG: "
    show_action = True
    show_pkg = True

    def __init__(self):
        self.ret_default = {
            'current': 0,
            'total': 0,
            'category': "",
            'pkg': "",
            'action': "",
            'is_running': False}

    def _emergeRunning(self):
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
            raise Exception("emerge not installed")

    def _getProgress(self):
        """
        Get current progress of emerge.

        returns a dict containing current and total value.
        """
        emerge_log_file = '/var/log/emerge.log'

        ret = {}

        input_data = []

        """
        Try to open file, if unable throw error to be catched later
        """
        try:
            with open(emerge_log_file, 'r') as fp:
                input_data = fp.readlines()
        except IOError as err:
            raise Exception(err)

        """
        Traverse emerge.log from bottom up to get latest information
        """

        input_data.reverse()

        for line in input_data:
            if "*** terminating." in line:
                # Copy content of ret_default no only the references
                ret = copy.deepcopt(self.ret_default)
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
        response['is_running'] = self._emergeRunning()
        ret = copy.deepcopy(self.ret_default)
        if response['is_running']:
            ret = self._getProgress()
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
