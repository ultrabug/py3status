# -*- coding: utf-8 -*-
"""
Display bluetooth status.

Confiuration parameters:
    - format : format when there is a connected device
    - format_no_conn : format when there is no connected device
    - format_no_conn_prefix : prefix when there is no connected device
    - format_prefix : prefix when there is a connected device

Format of status string placeholders
    {name} : device name
    {mac} : device MAC address

Requires:
    - hcitool

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
    color_bad = None
    color_good = None
    format = '{name}'
    format_no_conn = 'OFF'
    format_no_conn_prefix = 'BT: '
    format_prefix = 'BT: '
    separator = '|'

    def bluetooth(self, i3s_output_list, i3s_config):
        """
        The whole command:
        hcitool name `hcitool con | sed -n -r 's/.*([0-9A-F:]{17}).*/\\1/p'`
        """
        out = check_output(shlex.split('hcitool con'))
        macs = re.findall(BTMAC_RE, out.decode('utf-8'))
        color = self.color_bad or i3s_config['color_bad']

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
                data=self.separator.join(data)
            )

            color = self.color_good or i3s_config['color_good']
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
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.bluetooth([], config))
        sleep(1)
