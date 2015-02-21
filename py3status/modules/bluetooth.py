#!/usr/bin/env python
# encoding: utf-8

"""
Module for displaying bluetooth status

Requires:
    - hcitool
    - sed

@author jmdana <https://github.com/jmdana>
@license GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>
"""

from time import time
import subprocess
import shlex

class Py3status:
    # configuration parameters
    cache_timeout = 10
    color_good = None
    color_bad = None

    def __init__(self):
        pass

    def kill(self, i3s_output_list, i3s_config):
        pass

    def on_click(self, i3s_output_list, i3s_config, event):
        pass

    def get_status(self, i3s_output_list, i3s_config):
        # The whole command:
        # hcitool name `hcitool con | sed -n -r 's/.*([0-9A-F:]{17}).*/\\1/p'`

        cmd1 = shlex.split("hcitool con")
        cmd2 = shlex.split("sed -n -r 's/.*([0-9A-F:]{17}).*/\\1/p'")
        output = "BT: "
        color = self.color_bad or i3s_config['color_bad']

        p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)

        mac = p2.communicate()[0].strip().decode("utf-8")

        if mac != "":
            cmd3 = shlex.split("hcitool name %s" % mac)
            p3 = subprocess.Popen(cmd3, stdout=subprocess.PIPE)
            output += p3.communicate()[0].strip().decode("utf-8")
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
        print(x.get_status([], config))
        sleep(1)
