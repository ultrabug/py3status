# -*- coding: utf-8 -*-
"""
Display the unread feed items in your OwnCloud/NextCloud account.

You can also decide to check only for specific feeds or folders of feeds. To use this
feature, you have to first get the IDs of those feeds or folders. You can get those IDs
by clicking on the desired feed or folder and watching the URL:
```
https://yourcloudinstance.com/index.php/apps/news/#/items/feeds/FEED_ID
https://yourcloudinstance.com/index.php/apps/news/#/items/folders/FOLDER_ID

```
If both feeds list and folders list are left empty, all unread feed items will be counted.
Counted items don't need to match both feeds and folders lists. Items matching both a
given feed ID and a given folder ID will be counted only once.

Configuration parameters:
    aggregator: feed aggregator used, see note below. For now, the only supported value is
        `'owncloud'`, that means that you'll only be able to configure a
        OwnCloud/NextCloud instance. Other feed aggregator may be supported in future
        releases. (default 'owncloud')
    cache_timeout: how often to run this check (default 60)
    feed_ids: list of IDs of feeds to watch, see note below (default [])
    folder_ids: list of IDs of folders ro watch (default [])
    format: format to display (default 'Feed: {unseen}')
    password: login password (default '<PASSWORD>')
    server: aggregator server to connect to (default 'https://yourcloudinstance.com')
    user: login user (default '<USERNAME>')

Format placeholders:
    {unseen} sum of numbers of unread feed elements

Color options:
    color_new_items: text color when there is new items (default color_good)
    color_error: text color when there is an error (default color_bad)

Requires:
    python-requests: library to make web requests

@author raspbeguy
"""

import requests


class Py3status:
    """
    """
    # available configuration parameters
    aggregator = 'owncloud'
    cache_timeout = 60
    feed_ids = []
    folder_ids = []
    format = 'Feed: {unseen}'
    password = '<PASSWORD>'
    server = 'https://yourcloudinstance.com'
    user = '<USERNAME>'

    def post_config_hook(self):
        if self.aggregator not in ['owncloud']:  # more options coming
            raise ValueError('%s is not a supported feed aggregator' % self.aggregator)
        if self.aggregator == "owncloud":
            self._verify_owncloud()

    def _verify_owncloud(self):
        api_url = "%s/index.php/apps/news/api/v1-2/" % self.server
        try:
            r = requests.get(api_url + "feeds",
                             auth=(self.user, self.password),
                             timeout=1)
        except requests.exceptions.MissingSchema:
            raise ValueError('Unconsistent server URL')
        except requests.exceptions.ConnectionError:
            raise ValueError('Cannot resolve URL')
        except requests.exceptions.ConnectTimeout:
            raise ValueError('Timeout reached')
        if r.status_code != 200:
            raise ValueError('Not sure this is a Owncloud/Nextcloud instance')
        try:
            r.json()
        except:
            raise ValueError('Server returning bad content, possible bad credentials')

    def check_news(self):
        if self.aggregator == "owncloud":
            rss_count = self._get_count_owncloud()

        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        if rss_count == 'Error':
            response['full_text'] = rss_count
            response['color'] = self.py3.COLOR_ERROR or self.py3.COLOR_BAD
        elif rss_count != 0:
            response['color'] = self.py3.COLOR_NEW_ITEMS or self.py3.COLOR_GOOD
            response['full_text'] = self.py3.safe_format(
                self.format, {'unseen': rss_count}
            )
        else:
            response['full_text'] = self.py3.safe_format(
                self.format, {'unseen': rss_count}
            )

        return response

    def _get_count_owncloud(self):
        try:
            rss_count = 0
            api_url = "%s/index.php/apps/news/api/v1-2/" % self.server
            r = requests.get(api_url + "feeds",
                             auth=(self.user, self.password),
                             timeout=1)
            for feed in r.json()["feeds"]:
                if (
                    (not self.feed_ids and not self.folder_ids) or
                    feed["id"] in self.feed_ids or
                    feed["folderId"] in self.folder_ids
                ):
                    rss_count += feed["unreadCount"]

            return rss_count

        except requests.exceptions.MissingSchema:
            return 'Error'


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
