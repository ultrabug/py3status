# -*- coding: utf-8 -*-
"""
Display the total number of open tickets from GLPI.

Configuration parameters:
    - critical : set bad color above this threshold
    - db : database to use
    - host : database host to connect to
    - password : login password
    - user : login user
    - warning : set degraded color above this threshold

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.
"""

# You need MySQL-python from http://pypi.python.org/pypi/MySQL-python
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
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.count_glpi_open_tickets([], config))
        sleep(1)
