# -*- coding: utf-8 -*-
"""
Display number of ongoing tickets from RT queues.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 300)
    db: database to use (default '')
    format: see placeholders below (default 'general: {General}')
    host: database host to connect to (default '')
    password: login password (default '')
    thresholds: specify color thresholds to use
        (default [(0, None), (10, "degraded"), (20, "bad")])
    timeout: timeout for database connection (default 5)
    user: login user (default '')

Format placeholders:
    {YOUR_QUEUE_NAME} number of ongoing RT tickets (open+new+stalled)

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Requires:
    PyMySQL: https://pypi.org/project/PyMySQL/
        or
    MySQL-python: https://pypi.org/project/MySQL-python/

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
    thresholds = [(0, None), (10, "degraded"), (20, "bad")]
    timeout = 5
    user = ""

    def post_config_hook(self):
        self.thresholds_init = self.py3.get_color_names_list(self.format)
        # deprecate threshold configs
        if not self.thresholds_init:
            if self.thresholds == [(0, None), (10, "degraded"), (20, "bad")]:
                self.thresholds = [
                    (0, None),
                    (getattr(self, "threshold_warning", 10), "degraded"),
                    (getattr(self, "threshold_critical", 20), "bad"),
                ]

    def rt(self):
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
        queued = []
        for row in mycr.fetchall():
            queue, nb_tickets = row
            if queue == "___Approvals":
                continue
            tickets[queue] = nb_tickets
            if queue in self.format:
                queued.append(nb_tickets)

        for x in self.thresholds_init:
            if x in tickets:
                self.py3.threshold_get_color(tickets[x], x)
        if not self.thresholds_init:
            response["color"] = self.py3.threshold_get_color(max(queued))

        if queued:
            response["full_text"] = self.py3.safe_format(self.format, tickets)
        else:
            response["full_text"] = "queue(s) not found ({})".format(self.format)
        mydb.close()

        response["cached_until"] = self.py3.time_in(self.cache_timeout)
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
