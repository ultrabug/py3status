# -*- coding: utf-8 -*-
"""
Display MySQL/MariaDB slave state.

This module displays the number of seconds the slave is behind the master.

Configuration parameters:
    cache_timeout: refresh cache_timeout for this module (default 5)
    format_fail: format used for master_servers
      (default '[\?color=seconds_behind_master {host} is master]')
    format_ok: format used for slave servers
      (default '[\?color=seconds_behind_master {host} is {seconds_behind_master}s behind]')
    host: the host to connect to (default None)
    passwd: the password to use for the connection (default None)
    port: the port to connect to (default 3306)
    query: The sql query to run (default 'show slave status')
    thresholds: a threshold list of tuples, -1 used for a master hosts
        (default {'seconds_behind_master':
            [(0, 'deepskyblue'), (100, 'good'), (300, 'degraded'), (600, 'bad')]
        })
    user: the user used for the connection (default None)

Requires:
    MySQLdb: python package for python

@author cereal2nd
@license BSD

SAMPLE OUTPUT
{'full_text': 'test is 0s behind'}
{'full_text': 'test is 509s behind'}
{'full_text': 'test is master'}
"""

from __future__ import absolute_import
from MySQLdb import connect


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format_fail = '[\?color=seconds_behind_master {host} is master]'
    format_ok = '[\?color=seconds_behind_master {host} is {seconds_behind_master}s behind]'
    host = None
    passwd = None
    port = 3306
    query = 'show slave status'
    thresholds = {
        'seconds_behind_master': [
            (0, 'deepskyblue'),
            (100, 'good'),
            (300, 'degraded'),
            (600, 'bad')
        ]
    }
    user = None

    def _get_mysql_data(self):
        '''Returns a dictionary of the query output.'''
        conn = connect(user=self.user, passwd=self.passwd, host=self.host, port=self.port)
        cur = conn.cursor()
        cur.execute(self.query)
        keys = [desc[0].lower() for desc in cur.description]
        values = [str(val) for val in cur.fetchone()]
        conn.close()
        return dict(zip(keys, values))

    def mysql_slave(self):
        try:
            data = self._get_mysql_data()
            for k, v in data.items():
                self.py3.threshold_get_color(data[k], k)
            form = self.format_ok
        except:
            data = {}
            form = self.format_fail

        data['host'] = self.host

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(form, data)
        }


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
