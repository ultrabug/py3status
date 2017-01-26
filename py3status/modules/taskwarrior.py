# -*- coding: utf-8 -*-
"""
Display tasks currently running in taskwarrior.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 5)
    format: display format for taskwarrior (default '{task}')

Format placeholders:
    {task} active tasks

Requires
    task: https://taskwarrior.org/download/

@author James Smith http://jazmit.github.io/
@license BSD
"""

# import your useful libs here
from subprocess import check_output
import json
import shlex


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = '{task}'

    def taskWarrior(self):
        command = 'task start.before:tomorrow status:pending export'
        taskwarrior_output = check_output(shlex.split(command))
        tasks_json = json.loads(taskwarrior_output.decode('utf-8'))

        def describeTask(taskObj):
            return str(taskObj['id']) + ' ' + taskObj['description']

        result = ', '.join(map(describeTask, tasks_json))
        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'task': result})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
