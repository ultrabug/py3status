# -*- coding: utf-8 -*-
"""
Display MySQL/MariaDB slave state.

This module displays the number of seconds the slave is behind the master.

Configuration parameters:
    cache_timeout: refresh cache_timeout for this module (default 5)
    database: The type of module where we need to call the conenct method from
        (default 'MySQLdb')
    format: display format for this module
        *(default '\?color=seconds_behind_master {host} is '
              '[{seconds_behind_master}s behind|\?show master]')*
    parameters: The parameters needed for the connect function
        (default {'user': None, 'port': None, 'passwd': None, 'host': None})
    query: The sql query to run (default 'show slave status')
    thresholds: a threshold list of tuples, -1 used for a master hosts
        (default {'seconds_behind_master':
            [(0, 'deepskyblue'), (100, 'good'), (300, 'degraded'), (600, 'bad')]
        })

Requires:
    MySQLdb: python package for python

@author cereal2nd
@license BSD

SAMPLE OUTPUT
{'full_text': 'test is 0s behind'}
{'full_text': 'test is 509s behind'}
{'full_text': 'test is master'}
"""

from importlib import import_module


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    database = 'MySQLdb'
    format = ('\?color=seconds_behind_master {host} is '
              '[{seconds_behind_master}s behind|\?show master]')
    parameters = {
        'host': None,
        'user': None,
        'passwd': None,
        'port': None,
    }
    query = 'show slave status'
    thresholds = {
        'seconds_behind_master': [
            (0, 'deepskyblue'),
            (100, 'good'),
            (300, 'degraded'),
            (600, 'bad')
        ]
    }

    def post_config_hook(self):
        if not self.database:
            raise Exception('Missing database')
        if not self.parameters:
            raise Exception('Missing parameters')
        self.connect = getattr(import_module(self.database), 'connect')

    def _get_sql_data(self):
        '''Returns a dictionary of the query output.'''
        conn = self.connect(**self.parameters)
        cur = conn.cursor()
        cur.execute(self.query)
        keys = [desc[0].lower() for desc in cur.description]
        values = [str(val) for val in cur.fetchone()]
        conn.close()
        return dict(zip(keys, values))

    def sql(self):
        try:
            data = self._get_sql_data()
        except:
            data = {}
        data['host'] = self.parameters['host']

        for k, v in data.items():
            self.py3.threshold_get_color(data[k], k)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, data)
        }


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
