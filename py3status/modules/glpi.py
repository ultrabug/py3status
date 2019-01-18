"""
Display number of open tickets from GLPI.

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 300)
    critical: set bad color above this threshold (default 20)
    db: database to use (default '')
    format: format of the module output (default '{tickets_open} tickets')
    host: database host to connect to (default '')
    password: login password (default '')
    timeout: timeout for database connection (default 5)
    user: login user (default '')
    warning: set degraded color above this threshold (default 15)

Format placeholders:
    {tickets_open} The number of open tickets

Color options:
    color_bad: Open ticket above critical threshold
    color_degraded: Open ticket above warning threshold

Requires:
    MySQL-python: https://pypi.org/project/MySQL-python/

@author ultrabug

SAMPLE OUTPUT
{'full_text': '53 tickets'}
"""

import MySQLdb


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 300
    critical = 20
    db = ""
    format = "{tickets_open} tickets"
    host = ""
    password = ""
    timeout = 5
    user = ""
    warning = 15

    def glpi(self):
        response = {"full_text": ""}

        mydb = MySQLdb.connect(
            host=self.host,
            user=self.user,
            passwd=self.password,
            db=self.db,
            connect_timeout=self.timeout,
        )
        mycr = mydb.cursor()
        mycr.execute(
            """select count(*)
                        from glpi_tickets
                        where closedate is NULL and solvedate is NULL;"""
        )
        row = mycr.fetchone()
        if row:
            open_tickets = int(row[0])
            if open_tickets > self.critical:
                response.update({"color": self.py3.COLOR_BAD})
            elif open_tickets > self.warning:
                response.update({"color": self.py3.COLOR_DEGRADED})
            response["full_text"] = self.py3.safe_format(
                self.format, {"tickets_open": open_tickets}
            )
        mydb.close()
        response["cached_until"] = self.py3.time_in(self.cache_timeout)

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
