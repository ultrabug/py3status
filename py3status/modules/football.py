# -*- coding: utf-8 -*-
"""
This module print the match of your competition of football.
First step:
- register in https://www.football-data.org/client/register
- get your token
Then, you just need to choose:
- the competition: ligue 1 - premier leaqgue - bundesliga - liga
- the date: todat / tomorrow / aftertomorrow
"""
import http.client
import json
from datetime import timedelta
from datetime import date
from datetime import datetime

today = datetime.now()

class Py3status:

    def __init__(self):
        self.click = None
        self.state = 0
        self.token = None
        self.competition = None
        self.dateOfmatch = None

    def _connection(self):
        competitions = {
            "ligue 1": 2015,
            "premier league": 2021,
            "bundesliga": 2002,
            "liga": 2014
            }
        if self.dateOfmatch == "tomorrow":
            date = today + timedelta(days=1)
        elif self.dateOfmatch == "aftertomorrow":
            date = today + timedelta(days=2)
        else:
            date = today
        try:
            connection = http.client.HTTPConnection('api.football-data.org')
            headers = {'X-Auth-Token': self.token}
            uri = '/v2/competitions/%s/matches?dateFrom=%s&dateTo=%s' % (
                competitions[self.competition],
                date.date(),
                date.date()
                )
            self.py3.log(uri)
            connection.request('GET', uri, None, headers)
            response = json.loads(connection.getresponse().read().decode())

            return response
        except Exception as e:
            msg = "Error: calling api (%s)" % (str(e))
            self.py3.log(msg)

    def sport(self):
        self.py3.log("## starting Sport function")
        self.py3.log(today.date())

        # If no data storage, or last modification older today
        # => clean storage then call api.
        try:
            shift = 0
            if not self.py3.storage_get('_mtime') \
               or date.fromtimestamp(self.py3.storage_get('_mtime')) != today.date():
                self.py3.log(self.py3.storage_keys())
                for index in self.py3.storage_keys():
                    self.py3.log(index)
                    self.py3.storage_del(str(index))
                response = self._connection()
                # Retrieve the match and create the data storage
                if response:
                    for i in response['matches']:
                        format = ("%s - %s" % (
                            i['homeTeam']['name'],
                            i['awayTeam']['name'])
                        )
                        self.py3.storage_set(str(shift), format)
                        shift += 1
        except self.py3.Py3Exception as e:
            msg = "Error: creation data storage (%s)" % (str(e))
            self.py3.log(msg)

        # If the user click on the module,
        # retrive the next index of the data storage.
        try:
            if self.click == 1:
                if self.py3.storage_get(str(self.state)):
                    value = self.py3.storage_get(str(self.state))
                else:
                    self.state = 0
                    value = self.py3.storage_get(str(self.state))
                self.click = 0
            else:
                value = self.py3.storage_get('0')
        except Py3Exception as e:
            msg = "Error: click event (%s)" % (str(e))
            self.py3.log(msg)

        # No match scheduled
        if not value:
            value = "No match scheduled"

        # yellow color
        color = '#ffd900'
        self.py3.time_in(60)

        return {
            'full_text': value,
            'color': color,
            'cached_until': self.py3.time_in(3600)
        }

    def on_click(self, event):
        self.click = 1
        self.state = self.state + 1

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        'always_show': True,
    }

    from py3status.module_test import module_test
    module_test(Py3status, config=config)
