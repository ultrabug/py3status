# -*- coding: utf-8 -*-
"""
Show your ratio on your favorite Gazelle-based private tracker.

This module can get various useful infos about you on a private tracker.
You can display your ratio, upload size, download size.
The only requirements are that the private tracker is based on the Gazelle framework,
for instance Apollo or Redacted, and that the sysops didn't block API access somehow.
This module can save session cookies, and it is advised to avoid too much opened sessions
that could potentially get you troubles due to a suspect activity.

Configuration parameters:
    baseurl: Base URL of the tracker (with protocol and no trailing slash)
        (default 'https://mytracker.stuff')
    cache_timeout: How often we refresh this module in seconds (default 60)
    cookiepath: Path of the file containing identification cookie, can be None if
        you want to create a new session at each load of the module
        (default '/var/tmp/gazelle_ratio_cookie.txt')
    format: See placeholders below (default 'Ratio: {ratio}')
    limit_required: minimum ratio tolerated by tracker (if defined, overrides value given
        by API, so you are just likely not to fill it) (default None)
    limit_warning: custom warning ratio (default 1)
    password: Account password (default '')
    username: Account username (default '')

Format placeholders:
    {ratio} account ratio
    {download} account download amount
    {upload} account upload amount
    {messages} number of unread messages
    {notifs} number of new notifications

Color options:
    color_ratio_ok: color when ration is bigger than 1 (default color_good)
    color_ratio_warning: color when ration is between required ratio and 1
        (available only when tracker has a dynamic required ratio (default color_warning)
    color_ratio_ko: color when ratio below required ratio (default color_bad)

@author raspbeguy <raspbeguy@hashtagueule.fr>
@license MIT
"""

from py3status.exceptions import RequestException

try:
    # Python 3
    from http.cookiejar import (CookieJar, MozillaCookieJar)
except ImportError:
    # Python 2
    from cookielib import (CookieJar, MozillaCookieJar)


class Py3status:
    """
    """

    # available configuration parameters
    baseurl = 'https://mytracker.stuff'
    cache_timeout = 60
    cookiepath = '/var/tmp/gazelle_ratio_cookie.txt'
    format = 'Ratio: {ratio}'
    limit_required = None
    limit_warning = 1
    password = ''
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
        try:
            self._cookiejar.save(ignore_discard=True)
        except IOError:
            self.py3.log(
                    "Cannot write cookie at %s" % self.cookiepath,
                    level=self.py3.LOG_WARNING
                    )
        except AttributeError:
            pass  # That means that no cookie pass has been set
        else:
            self.py3.log(
                    "Created cookie at %s" % self.cookiepath,
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
        if self.cookiepath:
            self._cookiejar = MozillaCookieJar(self.cookiepath)
            try:
                self._cookiejar.load(ignore_discard=True)
                self._index()  # just to try if saved cookie is good
            except IOError:
                self.py3.log(
                        "Cannot read cookie at %s" % self.cookiepath,
                        level=self.py3.LOG_INFO
                        )
                self._login()
            except RequestException:
                self.py3.log(
                        "Cookie invalid or outdated. Re-logging.",
                        level=self.py3.LOG_INFO
                        )
                self._login()
        else:
            self._cookiejar = CookieJar()

    def gazelle(self):
        index = self._index()
        if index['status'] != "success":
            msg = "Tracker failed to give me user info"
            self.py3.log(msg, level=self.py3.LOG_ERROR)
            raise RequestException(msg)
        result = index['response']
        data = {
            'ratio': result['userstats']['ratio'],
            'requiredratio': result['userstats']['requiredratio'],
            'download': self._readable_size(result['userstats']['downloaded']),
            'upload': self._readable_size(result['userstats']['uploaded']),
            'messages': result['notifications']['messages'],
            'notifs': result['notifications']['notifications']
            }
        if data['ratio'] >= self.limit_warning:
            color = self.py3.COLOR_RATIO_OK or self.py3.COLOR_GOOD
        elif data['ratio'] >= self.limit_required:
            color = self.py3.COLOR_RATIO_WARNING or self.py3.COLOR_DEGRADED
        else:
            color = self.py3.COLOR_RATIO_KO or self.py3.COLOR_BAD
        full_text = self.py3.safe_format(self.format, data)
        return {
            'full_text': full_text,
            'cached_until': self.py3.time_in(self.cache_timeout),
            'color': color
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
