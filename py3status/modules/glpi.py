# -*- coding: utf-8 -*-
"""
Display the total number of open tickets from GLPI.

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

Configuration parameters:
    critical: set bad color above this threshold
    db: database to use
    host: database host to connect to
    password: login password
    user: login user
    warning: set degraded color above this threshold

Color options:
    color_bad: Open ticket above critical threshold
    color_degraded: Open ticket above warning threshold

Requires:
    MySQL-python: http://pypi.python.org/pypi/MySQL-python
"""

import MySQLdb


class Py3status:
    """
    """
    # available configuration parameters
    critical = 20
    db = ''
    host = ''
    password = ''
    timeout = 5
    user = ''
    warning = 15

    def count_glpi_open_tickets(self):
        response = {'full_text': ''}

        mydb = MySQLdb.connect(
            host=self.host,
            user=self.user,
            passwd=self.password,
            db=self.db,
            connect_timeout=self.timeout,
        )
        mycr = mydb.cursor()
        mycr.execute('''select count(*)
                        from glpi_tickets
                        where closedate is NULL and solvedate is NULL;''')
        row = mycr.fetchone()
        if row:
            open_tickets = int(row[0])
            if open_tickets > self.critical:
                response.update({'color': self.py3.COLOR_BAD})
            elif open_tickets > self.warning:
                response.update(
                    {'color': self.py3.COLOR_DEGRADED}
                )
            response['full_text'] = '%s tickets' % open_tickets
        mydb.close()

        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
