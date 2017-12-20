# -*- coding: utf-8 -*-
"""
Display tasks in thunderbird calendar.

Configuration parameters:
    cache_timeout: how often we refresh usage in seconds (default: 120s)
    err_exception: error message when an exception is raised
    err_profile: error message regarding profile path and read access
    format: see placeholders below
    profile_path: path to the user thunderbird profile (not optional)

Format of status string placeholders:
    {completed} completed tasks
    {current} title of current running task (sorted by priority and stamp)
    {due} due tasks

Make sure to configure profile_path in your i3status config using the full
path or this module will not be able to retrieve any information from your
calendar.

ex: profile_path = "/home/user/.thunderbird/1yawevtp.default"

@author mrt-prodz
"""
from sqlite3 import connect
from os import access, R_OK
from time import time


class Py3status:
    # available configuration parameters
    cache_timeout = 120
    err_exception = 'error: calendar parsing failed'
    err_profile = 'error: profile not readable'
    format = 'tasks:[{due}] current:{current}'
    profile_path = ''

    def _response(self, text, color=None):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': text,
        }
        if color is not None:
            response['color'] = color

        return response

    # return calendar data
    def get_calendar(self, i3s_output_list, i3s_config):
        _err_color = i3s_config['color_bad']

        db = self.profile_path + '/calendar-data/local.sqlite'
        if not access(db, R_OK):
            return self._response(self.err_profile, _err_color)

        try:
            con = connect(db)
            cur = con.cursor()
            cur.execute('SELECT title, todo_completed FROM cal_todos '
                        'ORDER BY priority DESC, todo_stamp DESC')
            tasks = cur.fetchall()
            con.close()

            # task[0] is the task name, task[1] is the todo_completed column
            duetasks = [task[0] for task in tasks if task[1] is None]

            due = len(duetasks)
            completed = len(tasks) - due
            current = duetasks[0] if due else ''

            return self._response(self.format.format(due=due,
                                                     completed=completed,
                                                     current=current))
        except Exception:
            return self._response(self.err_exception, _err_color)

if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_degraded': '#00FFFF',
        'color_bad': '#FF0000'
    }
    print(x.get_calendar([], config))
