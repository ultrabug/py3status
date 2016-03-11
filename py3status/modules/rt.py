# -*- coding: utf-8 -*-
"""
Display the number of ongoing tickets from selected RT queues.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 300)
    threshold_critical: set bad color above this threshold
    db: database to use
    format: see placeholders below
    host: database host to connect to
    password: login password
    user: login user
    threshold_warning: set degraded color above this threshold

Format of status string placeholders:
    {YOUR_QUEUE_NAME} number of ongoing RT tickets (open+new+stalled)

Requires:
    - `PyMySQL` https://pypi.python.org/pypi/PyMySQL
        or
    - `MySQL-python` http://pypi.python.org/pypi/MySQL-python

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

@author ultrabug
"""

try:
    import pymysql as mysql
except:
    import MySQLdb as mysql
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 300
    threshold_critical = 20
    db = ''
    format = 'general: {General}'
    host = ''
    password = ''
    timeout = 5
    user = ''
    threshold_warning = 10

    def rt_tickets(self, i3s_output_list, i3s_config):
        has_one_queue_formatted = False
        response = {'full_text': ''}
        tickets = {}

        mydb = mysql.connect(
            host=self.host,
            user=self.user,
            passwd=self.password,
            db=self.db,
            connect_timeout=self.timeout, )
        mycr = mydb.cursor()
        mycr.execute('''select q.Name as queue, coalesce(total,0) as total
            from Queues as q
            left join (
                select t.Queue as queue, count(t.id) as total
                from Tickets as t
                where Status = 'new' or Status = 'open' or Status = 'stalled'
                group by t.Queue)
            as s on s.Queue = q.id
            group by q.Name;''')
        for row in mycr.fetchall():
            queue, nb_tickets = row
            if queue == '___Approvals':
                continue
            tickets[queue] = nb_tickets
            if queue in self.format:
                has_one_queue_formatted = True
                if nb_tickets > self.threshold_critical:
                    response.update({'color': i3s_config['color_bad']})
                elif (nb_tickets > self.threshold_warning and
                      'color' not in response):
                    response.update({'color': i3s_config['color_degraded']})
        if has_one_queue_formatted:
            response['full_text'] = self.format.format(**tickets)
        else:
            response['full_text'] = 'queue(s) not found ({})'.format(
                self.format)
        mydb.close()

        response['cached_until'] = time() + self.cache_timeout
        return response


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.rt_tickets([], config))
        sleep(1)
