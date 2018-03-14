# -*- coding: utf-8 -*-
"""
Display MySQL/MariaDB slave state.

This module displays the number of seconds the slave is behind the master.

Configuration parameters:
    cache_timeout: refresh cache_timeout for this module (default 10)
    format_slave: format used for slave servers
    format_master: format used for master_servers
    host: defaults to localhost
    passwd: defaults to None
    port: defaults to 3306
    thresholds: a threshold list of tuples
    user: defaults to None

Format placeholders:
    {host} {seconds} behind

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
    format_slave = '[\?color=seconds {host} is {sec}s behind]'
    format_master = '[\?color=seconds {host} is master]'
    thresholds = [
            (-1, 'blue'),
            (0, 'deepskyblue'),
            (100, 'good'),
            (300, 'degraded'),
            (600, 'bad')
        ]
    host = None
    user = None
    passwd = None
    port = 3306

    def mysql_slave(self):
        try:
            data = self._getSlaveStatus()
            sec = data['Seconds_Behind_Master']
            self.py3.threshold_get_color(sec, 'seconds')
            form = self.format_slave
        except:
            form = self.format_master
            sec = -1
            self.py3.threshold_get_color(sec, 'seconds')

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(form, {'sec': str(sec), 'host': self.host})
        }

    def _getSlaveStatus(self):
        '''Returns a dictionary of the 'SHOW SLAVE STATUS;' command output.'''
        try:
            conn = connect(user=self.user, passwd=self.passwd, host=self.host, port=self.port)
        except:
            print('Failed to connect.')
            exit(3)
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
