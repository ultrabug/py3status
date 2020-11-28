"""
Display number of todos and more for Thunderbird.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 60)
    format: display format for this module (default '{format_todo}')
    format_datetime: specify strftime formatting to use (default {})
    format_separator: show separator if more than one (default ' ')
    format_todo: display format for todos
        (default '\\?if=!todo_completed {title}')
    profile: specify a profile path, otherwise first available profile
        eg '~/.thunderbird/abcd1234.default' (default None)
    sort: specify a tuple, eg ('placeholder_name', reverse_boolean)
        to sort by; excluding placeholder indexes (default ())
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {todo_total}        eg 5
    {todo_completed}    eg 2
    {todo_incompleted}  eg 3
    {format_todo}       format for todos

format_todo placeholders:
    {index_total}       eg 1, 2, 3
    {index_completed}   eg 1, 2, 3
    {index_incompleted} eg 1, 2, 3
    {alarm_last_ack}    eg None, 1513291952000000
    {cal_id}            eg 966bd855-5e71-4168-8072-c98f244ed825
    {flags}             eg 4, 276
    {ical_status}       eg None, IN-PROCESS, COMPLETED
    {id}                eg 87e9bfc9-eaad-4aa6-ad5f-adbf6d7a11a5
    {last_modified}     eg 1513276147000000
    {offline_journal}   eg None
    {priority}          eg None, # None=None, 0=None, 1=High, 5=Normal, 9=Low
    {privacy}           eg None, CONFIDENTIAL
    {recurrence_id}     eg None
    {recurrence_id_tz}  eg None, UTC
    {time_created}      eg 1513276147000000
    {title}             eg New Task
    {todo_complete}     eg None
    {todo_completed}    eg None, 1513281528000000
    {todo_completed_tz} eg None, UTC
    {todo_due}          eg None, 1513292400000000
    {todo_due_tz}       eg None, America/Chicago
    {todo_entry}        eg None, 1513292400000000
    {todo_entry_tz}     eg None, America/Chicago
    {todo_stamp}        eg 1513276147000000

format_datetime placeholders:
    KEY: alarm_last_ack, last_modified, time_created, todo,
        todo_completed, todo_entry, todo_stamp
    VALUE: % strftime characters to be translated, eg '%b %d' ----> 'Dec 14'
    SEE EXAMPLE BELOW: "show incompleted titles with last modified time"

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    thunderbird: standalone mail and news reader

Examples:
```
# show number of incompleted titles
thunderbird_todos {
    format = '{todo_incompleted} incompleted todos'
}

# show rainbow number of incompleted titles
thunderbird_todos {
    format = '\\?color=todo_incompleted {todo_incompleted} todos'
    thresholds = [
        (1, '#bababa'), (2, '#ffb3ba'), (3, '#ffdfba'), (4, '#ffffba'),
        (5, '#baefba'), (6, '#baffc9'), (7, '#bae1ff'), (8, '#bab3ff')
    ]
}

# show rainbow incompleted titles
thunderbird_todos {
    format_todo = '\\?if=!todo_completed&color=index_incompleted {title}'
    thresholds = [
        (1, '#bababa'), (2, '#ffb3ba'), (3, '#ffdfba'), (4, '#ffffba'),
        (5, '#baefba'), (6, '#baffc9'), (7, '#bae1ff'), (8, '#bab3ff')
    ]
}

# show incompleted titles with last modified time
thunderbird_todos {
    format_todo = '\\?if=!todo_completed {title} {last_modified}'
    format_datetime = {
        'last_modified': '\\?color=degraded last modified %-I:%M%P'
    }
}

# show 'No todos'
thunderbird_todos {
    format = '{format_todo}|No todos'
}

# show completed titles and incompleted titles
thunderbird_todos {
    format_todo = '\\?if=todo_completed&color=good {title}|\\?color=bad {title}'
}

# make todo blocks
thunderbird_todos {
    format = 'TODO {format_todo}'
    format_todo = '\\?if=todo_completed&color=good \u25b0|\\?color=bad \u25b0'
    format_separator = ''
}

# display incompleted titles with any priority
thunderbird_todos {
    format_todo = '\\?if=!todo_completed [\\?if=priority>0 {title}]'
}

# colorize titles based on priorities
thunderbird_todos {
    format_todo = '\\?if=!todo_completed [\\?color=priority {title}]'
    thresholds = [(0, None), (1, 'red'), (5, None), (9, 'deepskyblue')]
}

# sort todos
thunderbird_todos {
    sort = ('last_modified', True) # sort by modified time: recent first
    sort = ('priority', True)      # sort by priority: high to low
    sort = ('title', False)        # sort by title: ABC to abc
}

# add your snippets here
thunderbird_todos {
    format = '...'
}
```

@author mrt-prodz, lasers

SAMPLE OUTPUT
{'full_text': 'New Task 1, New Task 2'}
"""

from sqlite3 import connect
from datetime import datetime
from pathlib import Path

STRING_NO_PROFILE = "missing profile"
STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 60
    format = "{format_todo}"
    format_datetime = {}
    format_separator = " "
    format_todo = r"\?if=!todo_completed {title}"
    profile = None
    sort = ()
    thresholds = []

    def post_config_hook(self):
        if not self.py3.check_commands("thunderbird"):
            raise Exception(STRING_NOT_INSTALLED)

        # first profile, please.
        if not self.profile:
            directory = Path("~/.thunderbird").expanduser()
            profile_ini = directory / "profiles.ini"
            profile = []
            with profile_ini.open() as f:
                for line in f:
                    if line.startswith("Path="):
                        profile.append(
                            "{}/{}".format(directory, line.split("Path=")[-1].strip())
                        )
            if not len(profile):
                raise Exception(STRING_NO_PROFILE)
            self.profile = profile[0]

        self.profile = Path(self.profile).expanduser()
        self.path = self.profile / "calendar-data/local.sqlite"

        self.init_datetimes = []
        for word in self.format_datetime:
            if (self.py3.format_contains(self.format_todo, word)) and (
                word in self.format_datetime
            ):
                self.init_datetimes.append(word)

        self.thresholds_init = {}
        for name in ["format", "format_todo"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def _get_thunderbird_todos_data(self):
        connection = connect(self.path)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM cal_todos")
        keys = [desc[0] for desc in cursor.description]
        todos_data = cursor.fetchall()
        cursor.close()
        connection.close()
        return [dict(zip(keys, values)) for values in todos_data]

    def _organize(self, data):
        # sort?
        if self.sort:
            data = sorted(data, key=lambda k: k[self.sort[0]], reverse=self.sort[1])
        # counts and indexes
        count = {"todo_total": 0, "todo_completed": 0, "todo_incompleted": 0}
        for todo_index, todo in enumerate(data, 1):
            count["todo_total"] += 1
            todo["index_total"] = todo_index
            todo["index_completed"] = todo["index_incompleted"] = None
            if todo["todo_completed"]:
                count["todo_completed"] += 1
                todo["index_completed"] = count["todo_completed"]
            else:
                count["todo_incompleted"] += 1
                todo["index_incompleted"] = count["todo_incompleted"]

        return data, count

    def _manipulate(self, data, count):
        new_data = []
        for todo in data:
            # datetimes
            for k in self.init_datetimes:
                if k in todo:
                    todo[k] = self.py3.safe_format(
                        datetime.strftime(
                            datetime.fromtimestamp(float(str(todo[k])[:-6])),
                            self.format_datetime[k],
                        )
                    )
            # thresholds
            for x in self.thresholds_init["format_todo"]:
                if x in todo:
                    self.py3.threshold_get_color(todo[x], x)

            new_data.append(self.py3.safe_format(self.format_todo, todo))

        for x in self.thresholds_init["format"]:
            if x in count:
                self.py3.threshold_get_color(count[x], x)

        format_separator = self.py3.safe_format(self.format_separator)
        format_todo = self.py3.composite_join(format_separator, new_data)

        return format_todo

    def thunderbird_todos(self):
        todo_data = self._get_thunderbird_todos_data()
        data, count = self._organize(todo_data)
        format_todo = self._manipulate(data, count)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format, dict(format_todo=format_todo, **count)
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
