# -*- coding: utf-8 -*-
"""
Display bluetooth status.

Confiuration parameters:
    format: format when there is a connected device
    format_no_conn: format when there is no connected device
    format_no_conn_prefix: prefix when there is no connected device
    format_prefix: prefix when there is a connected device
    device_separator: the separator char between devices (only if more than one
        device)

Format of status string placeholders
    {name} device name
    {mac} device MAC address

Color options:
    color_bad: Conection on
    color_good: Connection off

Requires:
    hcitool:

@author jmdana <https://github.com/jmdana>
@license GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>
"""

import re
import shlex

from subprocess import check_output
from time import time

BTMAC_RE = re.compile(r'[0-9A-F:]{17}')


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = '{name}'
    format_no_conn = 'OFF'
    format_no_conn_prefix = 'BT: '
    format_prefix = 'BT: '
    device_separator = '|'

    def bluetooth(self):
        """
        The whole command:
        hcitool name `hcitool con | sed -n -r 's/.*([0-9A-F:]{17}).*/\\1/p'`
        """
        out = check_output(shlex.split('hcitool con'))
        macs = set(re.findall(BTMAC_RE, out.decode('utf-8')))
        color = self.py3.COLOR_BAD

        if macs != []:
            data = []
            for mac in macs:
                out = check_output(shlex.split('hcitool name %s' % mac))
                fmt_str = self.format.format(
                    name=out.strip().decode('utf-8'),
                    mac=mac
                )
                data.append(fmt_str)

            output = '{format_prefix}{data}'.format(
                format_prefix=self.format_prefix,
                data=self.device_separator.join(data)
            )

            color = self.py3.COLOR_GOOD
        else:
            output = '{format_prefix}{format}'.format(
                format_prefix=self.format_no_conn_prefix,
                format=self.format_no_conn
            )

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': output,
            'color': color,
        }

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
