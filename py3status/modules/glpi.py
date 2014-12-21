# -*- coding: utf-8 -*-
"""
This example class demonstrates how to display the current total number of
open tickets from GLPI in your i3bar.

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

Note that we don't have to implement a cache layer as it is handled by
py3status automagically.
"""

# You need MySQL-python from http://pypi.python.org/pypi/MySQL-python
import MySQLdb


class Py3status:

    # available configuration parameters
    critical = 20
    db = ''
    host = ''
    password = ''
    timeout = 5
    user = ''
    warning = 15

    def count_glpi_open_tickets(self, i3s_output_list, i3s_config):
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
            if i3s_config['colors']:
                if open_tickets > self.critical:
                    response.update({'color': i3s_config['color_bad']})
                elif open_tickets > self.warning:
                    response.update(
                        {'color': i3s_config['color_degraded']}
                    )
            response['full_text'] = '%s tickets' % open_tickets
        mydb.close()

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.count_glpi_open_tickets([], {}))
        sleep(1)
