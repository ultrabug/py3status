# -*- coding: utf-8 -*-
"""
Display data stored in MariaDB, MySQL, sqlite3, and hopefully more.

Configuration parameters:
    cache_timeout: refresh cache_timeout for this module (default 10)
    database: specify a database name to import (default None)
    format: display format for this module (default None)
    parameters: specify connection parameters to use (default None)
    query: specify a command to query on the database (default None)
    thresholds: specify color thresholds to use (default [])

Requires:
    mariadb: fast sql database server, drop-in replacement for mysql
    mysql-python: mysql support for python
    sqlite: a c library that implements an sql database engine

Examples:
```
# specify a database name to import
sql {
    database = 'sqlite3'  # from sqlite3 import connect
    database = 'MySQLdb'  # from MySQLdb import connect
    database = '...'      # from ... import connect
}

# specify connection parameters to use
http://mysql-python.sourceforge.net/MySQLdb.html#functions-and-attributes
https://docs.python.org/3/library/sqlite3.html#module-functions-and-constants
sql {
    name = 'MySQLdb'
    parameters = {
        'host': 'host', 'passwd': 'password', ...
    }
}

# specify a command to query on the database
sql {
    query = 'SHOW SLAVE STATUS'
    query = 'SELECT * FROM cal_todos'
    query = '...'
}

# real example, display number of seconds behind master with MySQLdb
sql {
    database = 'MySQLdb'
    format = '\?color=seconds_behind_master {host} is '
    format += '[{seconds_behind_master}s behind|\?show master]'
    parameters = {'host': 'localhost', 'passwd': '********'}
    query = 'SHOW SLAVE STATUS'
    thresholds = [
        (0, 'deepskyblue'), (100, 'good'), (300, 'degraded'), (600, 'bad')
    ]
}

# real example, query thunderbird_todo title with sqlite3
sql {
    database = 'sqlite3'
    format = '{title}'
    query = 'SELECT * FROM cal_todos'
    parameters = '~/.thunderbird/user.default/calendar-data/local.sqlite'
}
```



@author cereal2nd
@license BSD

SAMPLE OUTPUT
{'full_text': '509 seconds behind master'}
{'full_text': 'master'}
"""

from importlib import import_module
from os.path import expanduser


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    database = None
    format = None
    parameters = None
    query = None
    thresholds = []

    def post_config_hook(self):
        for config_name in ['database', 'format', 'parameters', 'query']:
            if not getattr(self, config_name, None):
                raise Exception('missing %s' % config_name)
        self.connect = getattr(import_module(self.database), 'connect')
        self.is_param_a_string = isinstance(self.parameters, str)
        if self.is_param_a_string:
            self.parameters = expanduser(self.parameters)

    def _get_sql_data(self):
        if self.is_param_a_string:
            conn = self.connect(self.parameters)
        else:
            conn = self.connect(**self.parameters)
        cur = conn.cursor()
        cur.execute(self.query)
        keys = [desc[0].lower() for desc in cur.description]
        values = [format(val) for val in cur.fetchone()]
        conn.close()
        return dict(zip(keys, values))

    def sql(self):
        sql_data = {}
        try:
            sql_data = self._get_sql_data()
        except:
            pass

        if self.thresholds:
            for k, v in sql_data.items():
                self.py3.threshold_get_color(v, k)

        if self.is_param_a_string:
            new_sql_data = sql_data
        else:
            new_sql_data = self.parameters.copy()
            new_sql_data.update(sql_data)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, new_sql_data)
        }


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
