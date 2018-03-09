# -*- coding: utf-8 -*-
"""
Display MYSQL slave state.

This module displays the number of secodns the slave is behind the master.

Configuration parameters:
    interval: refresh interval for this module (default 10)
    format: display format for this module (default 'SELinux: {state}')
    warning_threshold: defaults to 100
    critical_threshold: defaults to 200
    host: defaults to localhost
    user:
    passwd:
    port: defaults to 3306

Format placeholders:
    {host} {seconds} behind

Color options:
    color_bad: seconds behind master > critical_threshold
    color_degraded: warning_threshold < seconds behind master < critical_threshold
    color_good: seconds behind master < critical_threshold

Requires:
    MySQLdb: python package for python

@author cereal2nd
@license BSD

SAMPLE OUTPUT
{'full_text': 'test 0 seconds', 'color': '#00FF00'}

permissive
{'full_text': 'test 100 seconds', 'color': '#FFFF00'}

disabled
{'full_text': 'test 200 seconds', 'color': '#FF0000'}
"""

from __future__ import absolute_import
try:
    from MySQLdb import connect
except ImportError:
    print('Failed to import MySQLdb. Is mysqlclient installed?')
    exit(3)

class Py3status:
    """
    """
    # available configuration parameters
    interval = 5
    format = '{host} is {sec}s behind'
    warning_threshold = 100
    critical_threshold = 250
    host = ''
    user = ''
    passwd = ''
    port = 3306

    def mysql_slave(self):
        try:
            data = self._getSlaveStatus()
            sec = data['Seconds_Behind_Master']
            if sec > self.critical_threshold:
                color = self.py3.COLOR_BAD
            elif sec < self.warning_threshold:
                color = self.py3.COLOR_GOOD
            else:
                color = self.py3.COLOR_WARNING
            form = self.format
        except:
            form = "{host} is master"
            sec = -1
            color = self.py3.COLOR_GOOD

        return {
            'cached_until': self.py3.time_in(self.interval),
            'full_text': self.py3.safe_format(form, {'sec': str(sec), 'host': self.host}),
            'color': color
        }

    def _getSlaveStatus(self):
        '''Returns a dictionary of the 'SHOW SLAVE STATUS;' command output.'''
        try:
            conn = connect(user=self.user, passwd=self.passwd, host=self.host, port=self.port)
        except BaseException as e:
            print('Failed to connect.')
            exit(3)
        cur = conn.cursor()
        cur.execute('''SHOW SLAVE STATUS;''')
        keys = [desc[0] for desc in cur.description]
        values = cur.fetchone()
        return dict(zip(keys, values))

if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
