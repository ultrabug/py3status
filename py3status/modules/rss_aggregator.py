# -*- coding: utf-8 -*-
"""
Display the unread feed items in your OwnCloud/NextCloud account.

Configuration parameters:
    aggregator: feed aggregator used, see note below (default 'owncloud')
    cache_timeout: how often to run this check (default 60)
    feeds_id: list of IDs of feeds to watch, see note below (default [])
    folders_id: list of IDs of folders ro watch, see note below (default [])
    format: format to display (default 'Feed: {unseen}')
    hide_if_zero: don't show on bar if False (default False)
    new_items_color: text color when counter isn't zero (default '')
    password: login password (default '<PASSWORD>')
    server: IMAP server to connect to (default 'https://yourcloudinstance.com')
    user: login user (default '<USERNAME>')

Format placeholders:
    {unseen} sum of numbers of unread feed elements

For now, the only supported value of `aggregator` is `'owncloud'`, that means that you'll
only be able to configure a OwnCloud/NextCloud instance. Other feed aggregator may be
supported in future releases.

`feeds_id` and `folders_id` enable to restrict feed items counting to the given feeds and
folders IDs. You can get those ID by clicking on the desired feed or folder and watching
the URL:
```
https://yourcloudinstance.com/index.php/apps/news/#/items/feeds/FEED_ID
https://yourcloudinstance.com/index.php/apps/news/#/items/folders/FOLDER_ID

```
If both are left empty, all unread feed items will be counted. Counted items don't need
to match both feeds and folders lists. Items matching both a given feed ID and a given
folder ID will be counted only once.

@author raspbeguy
"""

import requests


class Py3status:
    """
    """
    # available configuration parameters
    aggregator = 'owncloud'
    cache_timeout = 60
    feeds_id = []
    folders_id = []
    format = 'Feed: {unseen}'
    hide_if_zero = False
    new_items_color = ''
    password = '<PASSWORD>'
    server = 'https://yourcloudinstance.com'
    user = '<USERNAME>'

    def post_config_hook(self):
        if self.aggregator not in ['owncloud']:  # more options coming
            raise ValueError('%s is not a supported feed aggregator' % self.aggregator)

    def check_news(self):
        if self.aggregator == "owncloud":
            rss_count = self._get_count_owncloud()

        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        if not self.new_items_color:
            self.new_items_color = self.py3.COLOR_GOOD

        if rss_count == 'Error':
            response['full_text'] = rss_count
            response['color'] = self.py3.COLOR_BAD
        elif rss_count != 0:
            response['color'] = self.new_items_color
            response['full_text'] = self.py3.safe_format(
                self.format, {'unseen': rss_count}
            )
        else:
            if self.hide_if_zero:
                response['full_text'] = ''
            else:
                response['full_text'] = self.py3.safe_format(
                    self.format, {'unseen': rss_count}
                )

        return response

    def _get_count_owncloud(self):
        try:
            rss_count = 0
            api_url = "%s/index.php/apps/news/api/v1-2/" % self.server
            r = requests.get(api_url + "feeds", auth=(self.user, self.password))
            for feed in r.json()["feeds"]:
                if (
                    (not self.feeds_id and not self.folders_id) or
                    feed["id"] in self.feeds_id or
                    feed["folderId"] in self.folders_id
                ):
                    rss_count += feed["unreadCount"]

            return rss_count

        except:
            return 'Error'


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
