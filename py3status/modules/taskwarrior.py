# -*- coding: utf-8 -*-
"""
Display tasks currently running in Taskwarrior.

Lo and behold. A swiss army knife of task management and/or customization
that can be done periodically! This module aims to support a wide range of
task customization needs if applicable. This covers the features available
in former taskwarrior module. With more options, we can perform more tricks.

This module welcomes more cowbell to make new customization possible.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    filter: specify one or more criteria to use (default None)
    format: display format for this module
        (default '[Task {format_task}]|No Task')
    format_annotation: display format for annotations (default None)
    format_annotation_separator: show separator if more than one (default ' ')
    format_datetime: specify strftime formatting to use (default {})
    format_tag: display format for tags (default None)
    format_tag_separator: show separator if more than one (default ' ')
    format_task: display format for tasks (default '{description}')
    format_task_separator: show separator if more than one (default ' ')
    sort_tasks: specify 2-tuples, eg ('placeholder_name', 'reverse_boolean'),
        to sort tasks by, excluding `index_task` placeholder (default ())
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {task} number of tasks, eg 5, 8, 10
    {context_name} active context name, eg work, study, home
    {context_filter} active context filter, eg +work, +study, +home
    {format_task} format for tasks, eg Task 1, Task 2

format_datetime placeholders:
    key: due, end, entry, modified, scheduled, start, until, wait
    value: % strftime characters to be translated, eg '%b %d' ----> 'Oct 06'

format_task placeholders:
    {index_task} index number, eg 1
    {id} id number, eg 1
    {tag} number of tags, eg 1
    {annotation} number of annotations, eg 1
    {description} description, eg Tell my friends about py3status
    {status} status, eg pending, deleted, completed, waiting, recurring
    {urgency} urgency measure, eg 0.147945
    {uuid} uuid, eg 90bbc3ae-60ea-4dbc-9d96-a029c4a92679
    {entry} entry date, eg 20171021T010203Z
    {modified} modified date, eg 20171021T010203Z
  * {start} start date, eg 20171021T010203Z
  * {end} end date, eg 20171021T010203Z
  * {due} due date, eg 20171021T010203Z
  * {until} until date, eg 20171021T010203Z
  * {wait} wait date, eg 20171021T010203Z
  * {scheduled} scheduled date, eg 20171021T010203Z
  * {recur} recurring unit, eg daily, weekly, monthly, yearly, etc
  * {mask} array of child status indicators, eg -, +, X, W
  * {imask} integer, eg 0
  * {parent} recurring parent uuid, eg 90bbc3ae-60ea-4dbc-9d96-a029c4a92679
  * {project} project name, eg py3status
  * {priority} priority, eg H, M, L
  * {depends} array of uuids, eg 90bbc3ae-60ea-4dbc-9d96-a029c4a92679
  * {format_tag} display format for tags
  * {format_annotation} display format for annotations

    The symbol `*` denotes optional and is absent if irrelevant to the task.
    In that case, we should always wrap them in square brackets, eg [{due}].
    For more information, see https://taskwarrior.org/docs/design/task.html

    User Defined Attributes (UDA) can be added too, eg [{estimate}].
    For more information, see https://taskwarrior.org/docs/udas.html

format_annotation placeholders:
    {index_annotation} index number, eg 1
    {entry} entry date, eg 20171021T010203Z
    {description} description, eg Tell my friends about py3status

format_tag placeholders:
    {index_tag} index number, eg 1
    {name} tag name, eg home, work

Color thresholds:
    format:
        task: print a color based on the number of tasks
    format_task:
        index_task: print a color based on the value of task index
        id: print a color based on the value of task id
        urgency: print a color based on the value of urgency
        tag: print a color based on the number of tags
        annotation: print a color based on the number of annotations
    format_tag:
        index_tag: print a color based on the value of tag index
    format_annotation:
        index_annotation: print a color based on the value of annotation index

Requires:
    task: a command-line todo list manager

Note:
    We can refresh a module with `py3-cmd` command.
    An example of using this command in a function.

    | ~/.{bash,zsh}{rc,_profile}
    | ---------------------------
    | function task () {
    |     command task "$@" && py3-cmd refresh taskwarrior
    | }

    With this, you can consider giving `cache_timeout` a much larger number,
    eg 3600 (an hour), so the module does not need to be updated that often.

Examples:
```
# filter the tasks
taskwarrior {
    filter = None                # show everything
    # filter = 'status:pending'  # show pending tasks
    # filter = '+ACTIVE'         # show tasks matching the virtual tags
    # filter = '+CONTEXT'        # show active context tasks (special custom)
    see `man task` for more information.
}

# show number of pending tasks
taskwarrior {
    format = '{task} pending tasks'
    filter = 'status:pending'
}

# add rainbow threshold
taskwarrior {
    thresholds = [
        (0, '#bababa'), (1, '#ffb3ba'), (2, '#ffdfba'), (3, '#ffffba'),
        (4, '#baefba'), (5, '#baffc9'), (6, '#bae1ff'), (7, '#bab3ff')
    ]
}

# show rainbow tasks
taskwarrior {
    format_task = '\?color=id {description}'
    format_task_separator = ', '
}

# show rainbow number of tasks
taskwarrior {
    format = '\?color=task {task} tasks'
}

# show colorized tasks based on urgency measure
taskwarrior {
    format_task = '\?color=urgency {description}'
    thresholds = [(0, None), (0.8, 'good'), (5, '#0ff'), (8, 'bad')]

    # The numbers in the urgency thresholds are merely an example and should
    # not be used as it is likely wrong and/or not accurate for a good reason.
    # For more information, see https://taskwarrior.org/docs/urgency.html
}

# add tags to the tasks
taskwarrior {
    format_task = '{description} {format_tag}'
    format_tag = '{name}'
    format_tag_separator = '\?color=#ff0 ,'
}

# colorize the tags... and if desired, rename the tags with symbols
# or icons like houses, skulls, or stars to represent your tags better
taskwarrior {
    format_task = '{format_tag}'
    format_tag = '[\?if=tag=home&color=good HOME|'
    format_tag += '[\?if=tag=work&color=bad WORK|'
    format_tag += '\?color=degraded {name}]]'
    format_tag_separator = ','
}

# colorize the projects... and if desired, rename the projects with symbols
# or icons like houses, skulls, or stars to represent your tags better
taskwarrior {
    format_task = '[\?if=project=home&color=good HOME|'
    format_task += '[\?if=project=work&color=bad WORK|'
    format_task += '\?color=degraded [{project}]]]'
    format_task_separator = ', '
}

# add yellow circled_triangle_down to the tagged tasks
taskwarrior {
    format_task = '{description}[ {format_tag}]'
    format_tag = '[\?if=tag&color=degraded \u238a]'
    format_tag_separator = ','
}

# add white flags to the annotations
taskwarrior {
    format_task = '{format_annotation}'
    format_annotation = '\u2690 {description}'
    format_annotation_separator = ' '
}

# add recurring symbol to the tasks
taskwarrior {
    format_task = '{description} [\?if=recur&show (R)]'
}

# add recurring duration unit to the tasks
taskwarrior {
    format_task = '{description} {recur}'
}

# add depends symbol to the tasks
taskwarrior {
    format_task = '{description} [\?if=depends&show (D)]'
}

# add urgency color to the tasks
taskwarrior {
    format_task = '{description} [\?color=urgency {urgency}]'
}

# sort tasks
taskwarrior {
    sort_tasks = ('modified', True)      # sort by modified time: recent first
    sort_tasks = ('description', False)  # sort by title: ABC to abc
    sort_tasks = ('urgency', True)       # sort by urgency: highest first
    sort_tasks = ('id', True)            # sort by id numbers: highest first
}

# display top 3 tasks sorted by urgency
taskwarrior {
    format_task = '\?if=index_task<4 [\?color=orange {description}]'
    format_task_separator = ', '
    sort_tasks = ('urgency', True)
}

# add your snippets here
taskwarrior {
    format = "..."
}
```

@author James Smith http://jazmit.github.io/, lasers
@license BSD

SAMPLE OUTPUT
{'full_text': '1 Prepare first draft, 2 Buy milk'}

rainbow
[
    {'full_text': 'New Task 1', 'color': '#FFB3BA'}, {'full_text': ', '},
    {'full_text': 'New Task 2', 'color': '#FFDFBA'}, {'full_text': ', '},
    {'full_text': 'New Task 3', 'color': '#FFFFBA'}, {'full_text': ', '},
]

no_task
{'full_text': 'No Task'}
"""

from json import loads as json_loads
from datetime import datetime

STRING_NOT_INSTALLED = 'not installed'
DATETIME = '%Y%m%dT%H%M%SZ'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    filter = None
    format = '[Task {format_task}]|No Task'
    format_annotation = None
    format_annotation_separator = ' '
    format_datetime = {}
    format_tag = None
    format_tag_separator = ' '
    format_task = '{description}'
    format_task_separator = ' '
    sort_tasks = ()
    thresholds = []

    def post_config_hook(self):
        if not self.py3.check_commands('task'):
            raise Exception(STRING_NOT_INSTALLED)

        self.task_command = 'task export'
        if self.filter:
            export_context = '+CONTEXT' in self.filter
            if export_context:
                self.filter = ' '.join(
                    [x.strip() for x in self.filter.split('+CONTEXT') if x]
                )
            if self.filter:
                self.task_command = 'task {} export'.format(self.filter)
        else:
            export_context = False

        self.init = {
            'annotations_and_tags': [], 'datetimes': [], 'thresholds': {},
            'context': self.py3.format_contains(self.format, 'context_*'),
            'export_context': export_context,
        }
        datetimes = [
            'due', 'end', 'entry', 'modified',
            'scheduled', 'start', 'until', 'wait'
        ]
        for name in ['annotations', 'tags']:
            placeholder = 'format_{}'.format(name[:-1])
            test_1 = self.py3.format_contains(self.format_task, placeholder)
            if test_1 and bool(getattr(self, placeholder)):
                self.init['annotations_and_tags'].append(name)

        for name in datetimes:
            test_1 = self.py3.format_contains(self.format_task, name)
            if test_1 and name in self.format_datetime:
                self.init['datetimes'].append(name)

        for name in ['format', 'format_task', 'format_annotation', 'format_tag']:
            self.init['thresholds'][name] = self.py3.get_color_names_list(
                getattr(self, name) or ''
            )

    def _get_context_data(self):
        context_name, context_filter = None, None
        if self.init['context'] or self.init['export_context']:
            line = self.py3.command_output('task context show')
            if 'No context is currently applied.' not in line:
                context_name, context_filter = line.split("'")[1::2]
        return context_name, context_filter

    def _get_task_data(self, context_filter):
        if self.init['export_context'] and context_filter:
            task_command = self.task_command + ' ' + context_filter
        else:
            task_command = self.task_command
        return json_loads(self.py3.command_output(task_command))

    def _manipulate(self, data):
        new_data = []

        if self.sort_tasks:
            key, reverse = self.sort_tasks[0], self.sort_tasks[1]
            data = sorted(data, key=lambda k: k[key], reverse=reverse)

        for task_index, task in enumerate(data, 1):
            task['index_task'] = task_index

            for name in self.init['datetimes']:
                task.setdefault(name, None)
                if task[name]:
                    task[name] = self.py3.safe_format(datetime.strftime(
                        datetime.strptime(task[name], DATETIME), task[name])
                    )

            for name in self.init['annotations_and_tags']:
                task.setdefault(name, [])
                if task[name]:
                    sname = name[:-1]
                    fn = 'format_{}'.format(sname)
                    if task[name]:
                        _list = []
                        _format = getattr(self, fn)
                        _separator = getattr(self, '{}_separator'.format(fn))
                        for index, data in enumerate(task[name], 1):
                            index_name = 'index_{}'.format(sname)
                            data = {'name': data} if name == 'tags' else data
                            data[index_name] = index
                            for _name in self.init['thresholds'][fn]:
                                if _name in data:
                                    self.py3.threshold_get_color(
                                        data[_name], _name
                                    )
                            _list.append(self.py3.safe_format(_format, data))
                        task[sname] = len(task[name])
                        task[fn] = self.py3.composite_join(_separator, _list)
                    else:
                        task[sname] = 0
                        task[fn] = None
                del task[name]

            for name in self.init['thresholds']['format_task']:
                if name in task:
                    self.py3.threshold_get_color(task[name], name)

            new_data.append(self.py3.safe_format(self.format_task, task))

        format_task_separator = self.py3.safe_format(self.format_task_separator)
        format_task = self.py3.composite_join(format_task_separator, new_data)

        return format_task

    def taskwarrior(self):
        context_name, context_filter = self._get_context_data()
        task_data = self._get_task_data(context_filter)

        taskwarrior_data = {
            'task': len(task_data),
            'format_task': self._manipulate(task_data),
            'context_name': context_name,
            'context_filter': context_filter,
        }

        for x in self.init['thresholds']['format']:
            if x in taskwarrior_data:
                self.py3.threshold_get_color(taskwarrior_data[x], x)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, taskwarrior_data)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
