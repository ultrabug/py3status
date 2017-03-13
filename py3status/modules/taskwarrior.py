# -*- coding: utf-8 -*-
"""
Display tasks currently running in taskwarrior.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module (default '{task}')

Format placeholders:
    {task} active tasks

Requires
    task: https://taskwarrior.org/download/

@author James Smith http://jazmit.github.io/
@license BSD

SAMPLE OUTPUT
{'full_text': '1 Prepare first draft, 2 Buy milk'}
"""

import json


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = '{task}'

    def taskWarrior(self):
        def describeTask(taskObj):
            return str(taskObj['id']) + ' ' + taskObj['description']

        task_command = 'task start.before:tomorrow status:pending export'
        task_json = json.loads(self.py3.command_output(task_command))
        task_result = ', '.join(map(describeTask, task_json))
        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'task': task_result})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
