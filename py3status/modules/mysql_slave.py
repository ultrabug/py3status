# -*- coding: utf-8 -*-
"""
Display MySQL/MariaDB slave state.

This module displays the number of seconds the slave is behind the master.

Configuration parameters:
    cache_timeout: refresh cache_timeout for this module (default 5)
    format_master: format used for master_servers
                    (default '[\\?color=seconds {host} is master]')
    format_slave: format used for slave servers
                    (default '[\\?color=seconds {host} is {seconds}s behind]')
    host: the host to connect to (default None)
    passwd: the password to use for the connection (default None)
    port: the port to connect to (default 3306)
    thresholds: a threshold list of tuples, -1 used for a master hosts
      (default [(-1, 'blue'), (0, 'deepskyblue'), (100, 'good'), (300, 'degraded'), (600, 'bad')])
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
    format_master = '[\?color=seconds {host} is master]'
    format_slave = '[\?color=seconds {host} is {seconds}s behind]'
    host = None
    passwd = None
    port = 3306
    thresholds = [
            (-1, 'blue'),
            (0, 'deepskyblue'),
            (100, 'good'),
            (300, 'degraded'),
            (600, 'bad')
        ]
    user = None

    def mysql_slave(self):
        try:
            data = self._get_slave_status()
            seconds = data['Seconds_Behind_Master']
            form = self.format_slave
        except:
            form = self.format_master
            seconds = -1
        self.py3.threshold_get_color(seconds, 'seconds')

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(form, {'seconds': str(seconds), 'host': self.host})
        }

    def _get_slave_status(self):
        '''Returns a dictionary of the 'SHOW SLAVE STATUS;' command output.'''
        conn = connect(user=self.user, passwd=self.passwd, host=self.host, port=self.port)
        cur = conn.cursor()
        cur.execute('''SHOW SLAVE STATUS;''')
        keys = [desc[0] for desc in cur.description]
        values = cur.fetchone()
        conn.close()
        return dict(zip(keys, values))


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
