# -*- coding: utf-8 -*-
"""
Emerge_status provides a short information on the current
emerge status if there is an emerge process currently running

Configuration parameters:
    cache_timeout: how often we refresh this module in second (default 0)
    format: Display format to user (default 'EMRG: {current} / {total}')
    hide_if_zero: Don't show in bar if there is no emerge running (default False)

Format placeholders:
    {current} Number of package that is currently emerged
    {total} Total number of packages that will be emerged
    {category} Category of the currently emerged package
    {pkg} Name of the currently emerged packaged
    {action} Current emerge action

Format examples:
     {current} / {total}'
    Result: "3 / 14"
    '{current} / {total} = {pkg}'
    Result: "3 / 14 = py3status"
    '{category} - {pkg}'
    Result: "x11-misc - py3status"

@author AnwariasEu
"""

import re


class Py3status:
    """
    """
    cache_timeout = 0
    format = u'EMRG: {current} / {total}'
    hide_if_zero = False

    def _emergeRunning(self):
        """
        Check if emerge is running.
        Returns true if at least one instance of emerge is running.
        """
        try:
            self.py3.command_output(['pgrep', 'emerge'])
            return True
        except:
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
        ret['current'] = None
        ret['total'] = None
        ret['category'] = None
        ret['pkg'] = None
        ret['action'] = None

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
                ret['current'] = "0"
                ret['total'] = "0"
                break
            else:
                match = re.search(">>> emerge.*", line)
                if match:
                    status_re = (
                        "\((?P<current>[0-9]+) of (?P<total>[0-9]+)\) "
                        "\((?P<action>[a-zA-Z0-9\/]+( [a-zA-Z0-9]+)?) "
                        "(?P<category>[a-zA-Z0-9\-]+)\/(?P<pkg>[a-zA-Z0-9\.]+)"
                    )
                    res = re.search(status_re, match.group())
                    if res:
                        ret['current'] = res.group('current')
                        ret['total'] = res.group('total')
                        ret['category'] = res.group('category')
                        ret['pkg'] = res.group('pkg')
                        ret['action'] = res.group('action')
                    break
        return ret

    def emerge_status(self):
        """
        Emerge Status main routine
        """
        response = {}
        response['cached_until'] = self.py3.time_in(self.cache_timeout)
        if self._emergeRunning():
            self.ret = self._getProgress()
            response['full_text'] = self.py3.safe_format(self.format, self.ret)
        else:
            if self.hide_if_zero:
                response['full_text'] = ""
            else:
                self.ret = {}
                self.ret['current'] = "0"
                self.ret['total'] = "0"
                self.ret['category'] = ""
                self.ret['pkg'] = ""
                self.ret['action'] = "None"
                response['full_text'] = self.py3.safe_format(
                    self.format, self.ret)

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
