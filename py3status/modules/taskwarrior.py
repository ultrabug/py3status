# -*- coding: utf-8 -*-
"""
Display tasks currently running in taskwarrior.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    filter: specify one or more criteria to use (default 'status:pending')
    format: display format for this module (default '{descriptions}')

Format placeholders:
    {descriptions} descriptions of active tasks
    {tasks} number of active tasks

Requires
    task: https://taskwarrior.org/download/

@author James Smith https://jazmit.github.io
@license BSD

SAMPLE OUTPUT
{'full_text': '1 Prepare first draft, 2 Buy milk'}
"""

import json

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    filter = "status:pending"
    format = "{descriptions}"

    class Meta:
        deprecated = {
            "rename_placeholder": [
                {
                    "placeholder": "task",
                    "new": "descriptions",
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        if not self.py3.check_commands("task"):
            raise Exception(STRING_NOT_INSTALLED)
        self.placeholders = self.py3.get_placeholders_list(self.format)
        if self.filter:
            self.taskwarrior_command = "task %s export" % self.filter
        else:
            self.taskwarrior_command = "task export"

    @staticmethod
    def descriptions(tasks_json):
        def _describeTask(taskObj):
            return str(taskObj["id"]) + " " + taskObj["description"]

        return ", ".join(map(_describeTask, tasks_json))

    @staticmethod
    def tasks(tasks_json):
        return len(tasks_json)

    def taskwarrior(self):
        tasks_json = json.loads(self.py3.command_output(self.taskwarrior_command))
        taskwarrior_data = {}
        for ph in self.placeholders:
            if hasattr(self, ph):
                ph_func = getattr(self, ph)
                taskwarrior_data[ph] = ph_func(tasks_json)
        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, taskwarrior_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
