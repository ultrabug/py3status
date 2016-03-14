# -*- coding: utf-8 -*-
"""
Display tasks in thunderbird calendar.

Configuration parameters:
    - cache_timeout : how often we refresh usage in seconds (default: 120s)
    - profile_path : path to the user thunderbird profile (not optional)
    - format : see placeholders below

Format of status string placeholders:
    {due} : due tasks
    {completed} : completed tasks
    {current} : title of current running task (sorted by priority and stamp)

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
    # user must configure the path to thunderbird profile_path
    # ex: /home/user/.thunderbird/1yawevtp.default
    profile_path = ''
    format = 'tasks:[{due}] current:{current}'

    # return error occurs
    def _error_response(self, color):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': 'Err',
            'color': color
        }
        return response

    # return calendar data
    def get_calendar(self, i3s_output_list, i3s_config):
        db = self.profile_path + '/calendar-data/local.sqlite'
        due = completed = 0
        current = ''
        if not access(db, R_OK):
            return self._error_response(i3s_config['color_bad'])

        try:
            con = connect(db)
            cur = con.cursor()
            cur.execute('SELECT title, todo_completed FROM cal_todos '
                        'ORDER BY priority DESC, todo_stamp DESC')
            tasks = cur.fetchall()
            con.close()

            # t = title, c = completed
            duetasks = [t for t in tasks for c in t if c is None]
            due = len(duetasks)
            completed = len(tasks) - due
            if due > 0 and type(duetasks[0] is tuple):
                current = duetasks[0][0]

            response = {
                'cached_until': time() + self.cache_timeout,
                'full_text': self.format.format(due=due,
                                                completed=completed,
                                                current=current)
            }
            return response
        except:
            return self._error_response(i3s_config['color_bad'])

if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_degraded': '#00FFFF',
        'color_bad': '#FF0000'
    }
    print(x.get_calendar([], config))
