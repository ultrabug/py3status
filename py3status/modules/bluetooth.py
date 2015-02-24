#!/usr/bin/env python
# encoding: utf-8

"""
Module for displaying bluetooth status

Requires:
    - hcitool

@author jmdana <https://github.com/jmdana>
@license GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>
"""

import re
import shlex
from subprocess import check_output
from time import time

BTMAC_RE = re.compile(r"[0-9A-F:]{17}")

class Py3status:
    # configuration parameters
    cache_timeout = 10
    color_good = None
    color_bad = None

    def bluetooth(self, i3s_output_list, i3s_config):
        # The whole command:
        # hcitool name `hcitool con | sed -n -r 's/.*([0-9A-F:]{17}).*/\\1/p'`

        out = check_output(shlex.split("hcitool con"))
        macs = re.findall(BTMAC_RE, out.decode("utf-8"))
        output = "BT: "
        color = self.color_bad or i3s_config['color_bad']

        if macs != []:
            names = []
            for mac in macs:
                out = check_output(shlex.split("hcitool name %s" % mac))
                names.append(out.strip().decode("utf-8"))

            output += "|".join(names)

            color = self.color_good or i3s_config['color_good']
        else:
            output += "OFF"

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
        "color_good": "#00FF00",
        "color_bad": "#FF0000",
        }

    while True:
        print(x.bluetooth([], config))
        sleep(1)
