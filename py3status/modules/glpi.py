# You need MySQL-python from http://pypi.python.org/pypi/MySQL-python
import MySQLdb


class Py3status:
    """
    This example class demonstrates how to display the current total number of
    open tickets from GLPI in your i3bar.

    It features thresholds to colorize the output and forces a low timeout to
    limit the impact of a server connectivity problem on your i3bar freshness.

    Note that we don't have to implement a cache layer as it is handled by
    py3status automagically.
    """
    def count_glpi_open_tickets(self, json, i3status_config):
        response = {'full_text': '', 'name': 'glpi_tickets'}

        # user-defined variables
        CRIT_THRESHOLD = 20
        WARN_THRESHOLD = 15
        MYSQL_DB = ''
        MYSQL_HOST = ''
        MYSQL_PASSWD = ''
        MYSQL_USER = ''
        POSITION = 0

        mydb = MySQLdb.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWD,
            db=MYSQL_DB,
            connect_timeout=5,
            )
        mycr = mydb.cursor()
        mycr.execute('''select count(*)
                        from glpi_tickets
                        where closedate is NULL and solvedate is NULL;''')
        row = mycr.fetchone()
        if row:
            open_tickets = int(row[0])
            if i3status_config['colors']:
                if open_tickets > CRIT_THRESHOLD:
                    response.update({'color': i3status_config['color_bad']})
                elif open_tickets > WARN_THRESHOLD:
                    response.update(
                        {'color': i3status_config['color_degraded']}
                    )
            response['full_text'] = '%s tickets' % open_tickets
        mydb.close()

        return (POSITION, response)
