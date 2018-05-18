# -*- coding: utf-8 -*-
"""
Display tasks currently running in taskwarrior.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    filter: specify one or more criteria to use (default 'status:pending')
    format: display format for this module (default '{task}')

Format placeholders:
    {task} active tasks
    {context} current active context
    {nb_tasks} number of active tasks

Requires
    task: https://taskwarrior.org/download/

@author James Smith http://jazmit.github.io/
@license BSD

SAMPLE OUTPUT
{'full_text': '1 Prepare first draft, 2 Buy milk'}
"""

import json
STRING_NOT_INSTALLED = 'not installed'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    filter = 'status:pending'
    format = '{task}'

    def post_config_hook(self):
        if not self.py3.check_commands('task'):
            raise Exception(STRING_NOT_INSTALLED)
        if self.filter:
            self.task_command = 'task %s export' % self.filter
        else:
            self.task_command = 'task export'

    def _get_context(self):
        context = "none"
        task_context = self.py3.command_output('task context show')
        if not task_context.startswith("No context"):
            context = task_context.split('\'')[1]
        return context

    def taskWarrior(self):
        def describeTask(taskObj):
            return str(taskObj['id']) + ' ' + taskObj['description']

        task_json = json.loads(self.py3.command_output(self.task_command))

        task_result = ', '.join(map(describeTask, task_json))
        nb_tasks = len(task_json)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'task': task_result,
                                                            'context': self._get_context(),
                                                            'nb_tasks': nb_tasks})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    config = {
        "format": "{task} {context} {nb_tasks}"
    }
    module_test(Py3status, config=config)
