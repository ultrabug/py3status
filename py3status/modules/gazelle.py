# -*- coding: utf-8 -*-
"""
Show your ratio on your favorite Gazelle-based private tracker.

This module can get various useful infos about you on a private tracker.
You can display your ratio, upload size, download size.
The only requirements are that the private tracker is based on the Gazelle framework,
for instance Apollo or Redacted, and that the sysops didn't block API access somehow.
This module will save session cookies to avoid too much opened sessions which could
potentially put you into troubles due to a suspect activity.

Configuration parameters:
    baseurl: Base URL of the tracker (example: https://what.cd) (default None)
    cache_timeout: How often we refresh this module in seconds (default 60)
    format: See placeholders below (default 'Ratio: {ratio}')
    password: Account password (default '')
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), ('requiredratio', 'degraded'), (1, 'good')])
    urgent_new_messages: set output urgent mode when there are new messages
        (default False)
    urgent_new_notifs: set output urgent mode when there are new notifications
        (default False)
    username: Account username (default '')

Format placeholders:
    {ratio} account ratio
    {download} account download amount
    {upload} account upload amount
    {messages} number of unread messages
    {notifs} number of new notifications

@author raspbeguy <raspbeguy@hashtagueule.fr>
@license MIT
"""

from py3status.exceptions import RequestException

import re


class Py3status:
    """
    """

    # available configuration parameters
    baseurl = None
    cache_timeout = 60
    format = 'Ratio: {ratio}'
    password = ''
    thresholds = [(0, 'bad'), ('requiredratio', 'degraded'), (1, 'good')]
    urgent_new_messages = False
    urgent_new_notifs = False
    username = ''

    def _readable_size(self, size):
        num = size
        for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB']:
            if abs(num) < 1024.0:
                return "%3.1f %s" % (num, unit)
            num /= 1024.0
        return "%.1f%s" % (num, 'YiB')

    def _login(self):
        self.py3.request(
                self.baseurl+"/login.php",
                data={'username': self.username, 'password': self.password},
                headers={'User-Agent': 'Mozilla/5.0'},
                cookiejar=self._cookiejar
                )
        try:
            self._index()  # just to try if login info are good
        except RequestException:
            self.py3.log(
                    "Cannot login to %s" % self.baseurl,
                    level=self.py3.LOG_ERROR
                    )
            raise
        self._cookiejar.save(self.baseurl)
        self.py3.log(
                "Saved cookie in storage",
                level=self.py3.LOG_INFO
                )

    def _index(self):
        resp = self.py3.request(
                self.baseurl+"/ajax.php",
                params={'action': "index"},
                headers={
                    'User-Agent': 'Mozilla/5.0'
                    },
                cookiejar=self._cookiejar
                )
        return resp.json()

    def post_config_hook(self):
        # Check if given URL is really an URL
        if not isinstance(self.baseurl, str) or not re.search("^https?://", self.baseurl):
            self.py3.error("Invalid URL")
        self.baseurl = self.baseurl.strip('/')
        if not isinstance(self.username, str) or not isinstance(self.password, str):
            self.py3.error("Invalid login info")
        # Make a copy of thresholds list with keywords
        self._thresholds_orig = list(self.thresholds)

        self._cookiejar = self.py3.storage_new_cookiejar()
        try:
            self._cookiejar.load(self.baseurl)
            self._index()  # just to try if saved cookie is good
        except RequestException:
            self.py3.log(
                    "Cookie invalid, outdated or missing. Re-logging.",
                    level=self.py3.LOG_INFO
                    )
            self._login()

    def gazelle(self):
        try:
            index = self._index()
            if index['status'] != "success":
                msg = "Tracker failed to give me user info"
                self.py3.log(msg, level=self.py3.LOG_ERROR)
                raise RequestException(msg)
        except RequestException:
            self.py3.error("Network error")

        result = index['response']
        data = {
            'ratio': result['userstats']['ratio'],
            'requiredratio': result['userstats']['requiredratio'],
            'download': self._readable_size(result['userstats']['downloaded']),
            'upload': self._readable_size(result['userstats']['uploaded']),
            'messages': result['notifications']['messages'],
            'notifs': result['notifications']['notifications']
            }

        # Ok, so if you think that what I'll do next stinks a bit, remember that
        # the color threshold design in py3status is a gigantic turd.
        # Main reason of this ugliness is the impossibility to natively define a
        # variable threshold, so I have to replace keyword by the actual value.
        for n, item in enumerate(self._thresholds_orig):
            if item[0] == "requiredratio":
                lst = list(item)
                lst[0] = data['requiredratio']
                self.thresholds[n] = tuple(lst)
        # End of horrible code

        self.py3.threshold_get_color(data['ratio'], 'ratio')

        full_text = self.py3.safe_format(self.format, data)
        return {
            'full_text': full_text,
            'cached_until': self.py3.time_in(self.cache_timeout),
            'urgent':
                (self.urgent_new_messages and bool(data['messages'])) or
                (self.urgent_new_notifs and bool(data['notifs']))
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
