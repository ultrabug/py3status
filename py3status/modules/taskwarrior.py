# -*- coding: utf-8 -*-

"""
Display currently active (started) taskwarrior tasks.

Configuration parameters:
    - cache_timeout : how often we refresh this module in seconds

Requires
    - jq
    - awk

@author James Smith http://jazmit.github.io/
@license BSD
"""

# import your useful libs here
from time import time
import subprocess

class Py3status:
    cache_timeout = 5

    def taskWarrior(self, i3s_output_list, i3s_config):
        active_task = subprocess.check_output(
            """task start.before:tomorrow status:pending export \
                | awk 'BEGIN { print "["} { print $0 } END { print "]"}' \
                | jq -r 'map( (.id | tostring) + " " + .description ) | join(", ")' \
            """,
            shell=True).strip()
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': active_task
        }
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.taskWarrior([], config))
        sleep(1)
