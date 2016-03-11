# -*- coding: utf-8 -*-
"""
Display currently active (started) taskwarrior tasks.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (5s default)

Requires
  - `task`

@author James Smith http://jazmit.github.io/
@license BSD
"""

# import your useful libs here
from time import time
from subprocess import check_output
import json
import shlex


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5

    def taskWarrior(self, i3s_output_list, i3s_config):
        command = 'task start.before:tomorrow status:pending export'
        taskwarrior_output = check_output(shlex.split(command))
        tasks_json = json.loads(taskwarrior_output.decode('utf-8'))

        def describeTask(taskObj):
            return str(taskObj['id']) + ' ' + taskObj['description']

        result = ', '.join(map(describeTask, tasks_json))
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': result
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
