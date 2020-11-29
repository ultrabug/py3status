"""
Display number of ongoing tickets from RT queues.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 300)
    db: database to use (default '')
    format: see placeholders below (default 'general: {General}')
    host: database host to connect to (default '')
    password: login password (default '')
    threshold_critical: set bad color above this threshold (default 20)
    threshold_warning: set degraded color above this threshold (default 10)
    timeout: timeout for database connection (default 5)
    user: login user (default '')

Format placeholders:
    {YOUR_QUEUE_NAME} number of ongoing RT tickets (open+new+stalled)

Color options:
    color_bad: Exceeded threshold_critical
    color_degraded: Exceeded threshold_warning

Requires:
    PyMySQL: https://pypi.org/project/PyMySQL/
        or
    MySQL-python: https://pypi.org/project/MySQL-python/

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

@author ultrabug

SAMPLE OUTPUT
{'full_text': 'general: 24'}
"""

try:
    import pymysql as mysql
except:  # noqa e722 // (ImportError, ModuleNotFoundError):  # py2/py3
    import MySQLdb as mysql


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 300
    db = ""
    format = "general: {General}"
    host = ""
    password = ""
    threshold_critical = 20
    threshold_warning = 10
    timeout = 5
    user = ""

    def rt(self):
        has_one_queue_formatted = False
        response = {"full_text": ""}
        tickets = {}

        mydb = mysql.connect(
            host=self.host,
            user=self.user,
            passwd=self.password,
            db=self.db,
            connect_timeout=self.timeout,
        )
        mycr = mydb.cursor()
        mycr.execute(
            """select q.Name as queue, coalesce(total,0) as total
            from Queues as q
            left join (
                select t.Queue as queue, count(t.id) as total
                from Tickets as t
                where Status = 'new' or Status = 'open' or Status = 'stalled'
                group by t.Queue)
            as s on s.Queue = q.id
            group by q.Name;"""
        )
        for row in mycr.fetchall():
            queue, nb_tickets = row
            if queue == "___Approvals":
                continue
            tickets[queue] = nb_tickets
            if queue in self.format:
                has_one_queue_formatted = True
                if nb_tickets > self.threshold_critical:
                    response.update({"color": self.py3.COLOR_BAD})
                elif nb_tickets > self.threshold_warning and "color" not in response:
                    response.update({"color": self.py3.COLOR_DEGRADED})
        if has_one_queue_formatted:
            response["full_text"] = self.py3.safe_format(self.format, tickets)
        else:
            response["full_text"] = f"queue(s) not found ({self.format})"
        mydb.close()

        response["cached_until"] = self.py3.time_in(self.cache_timeout)
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
