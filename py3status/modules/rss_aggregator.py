# -*- coding: utf-8 -*-
"""
Display unread feeds in your favorite RSS aggregator.

Configuration parameters:
    aggregator: feed aggregator used. Supported values are `owncloud` and `ttrss`.
        Other aggregators might be supported in future releases. Contributions are
        welcome. (default 'owncloud')
    cache_timeout: how often to run this check (default 60)
    feed_ids: list of IDs of feeds to watch, see note below (default [])
    folder_ids: list of IDs of folders ro watch (default [])
    format: format to display (default 'Feed: {unseen}')
    password: login password (default None)
    server: aggregator server to connect to (default 'https://yourcloudinstance.com')
    user: login user (default None)

Format placeholders:
    {unseen} sum of numbers of unread feed elements

Color options:
    color_new_items: text color when there is new items (default color_good)
    color_error: text color when there is an error (default color_bad)

Requires:
    requests: python module from pypi https://pypi.python.org/pypi/requests

Notes:
    You can also decide to check only for specific feeds or folders of feeds.
    To use this feature, you have to first get the IDs of those feeds or
    folders. You can get those IDs by clicking on the desired feed or folder
    and watching the URL.

    For OwnCloud/NextCloud with News application:
    https://yourcloudinstance.com/index.php/apps/news/#/items/feeds/FEED_ID
    https://yourcloudinstance.com/index.php/apps/news/#/items/folders/FOLDER_ID

    For Tiny Tiny RSS 1.6 or newer:
    https://yourttrssinstance.com/index.php#f=FEED_ID&c=0
    https://yourttrssinstance.com/index.php#f=FOLDER_ID&c=1

    If both feeds list and folders list are left empty, all unread feed items
    will be counted. You may use both feeds list and folders list, but given
    feeds shouldn't be included in given folders, else unread count number
    behavior is unpredictable. Same warning when aggregator allows subfolders:
    the folders list shouldn't include a folder and one of its subfolder.

@author raspbeguy

SAMPLE OUTPUT
{'full_text': 'Feed: 488'}
"""

import requests
import json


class Py3status:
    """
    """

    # available configuration parameters
    aggregator = "owncloud"
    cache_timeout = 60
    feed_ids = []
    folder_ids = []
    format = "Feed: {unseen}"
    password = None
    server = "https://yourcloudinstance.com"
    user = None

    def post_config_hook(self):
        self._cached = "?"
        if self.aggregator not in ["owncloud", "ttrss"]:  # more options coming
            raise ValueError("%s is not a supported feed aggregator" % self.aggregator)
        if self.user is None or self.password is None:
            raise ValueError("user and password must be provided")

    def rss_aggregator(self):
        if self.aggregator == "owncloud":
            rss_count = self._get_count_owncloud()
        elif self.aggregator == "ttrss":
            rss_count = self._get_count_ttrss()

        self._cached = self._cached if rss_count is None else rss_count

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"unseen": self._cached}),
        }

        if rss_count is None:
            response["color"] = self.py3.COLOR_ERROR or self.py3.COLOR_BAD
        elif rss_count != 0:
            response["color"] = self.py3.COLOR_NEW_ITEMS or self.py3.COLOR_GOOD

        return response

    def _get_count_owncloud(self):
        try:
            rss_count = 0
            api_url = "%s/index.php/apps/news/api/v1-2/" % self.server
            r = requests.get(
                api_url + "feeds", auth=(self.user, self.password), timeout=10
            )
            for feed in r.json()["feeds"]:
                if (
                    (not self.feed_ids and not self.folder_ids)
                    or feed["id"] in self.feed_ids
                    or feed["folderId"] in self.folder_ids
                ):
                    rss_count += feed["unreadCount"]

            return rss_count

        except:  # noqa e722
            return None

    def _get_count_ttrss(self):
        try:
            rss_count = 0
            api_url = "%s/api/" % self.server
            r = requests.post(
                api_url,
                data=json.dumps(
                    {"op": "login", "user": self.user, "password": self.password}
                ),
            )
            sid = r.json()["content"]["session_id"]
            if not self.feed_ids and not self.folder_ids:
                r = requests.post(
                    api_url, data=json.dumps({"sid": sid, "op": "getUnread"})
                )
                rss_count = r.json()["content"]["unread"]
            else:
                for folder in self.folder_ids:
                    r = requests.post(
                        api_url,
                        data=json.dumps(
                            {
                                "sid": sid,
                                "op": "getFeeds",
                                "cat_id": folder,
                                "include_nested": True,
                            }
                        ),
                    )
                    for item in r.json()["content"]:
                        rss_count += item["unread"]
                if self.feed_ids:
                    r = requests.post(
                        api_url,
                        data=json.dumps({"sid": sid, "op": "getFeeds", "cat_id": -3}),
                    )
                    for feed in r.json()["content"]:
                        if feed["id"] in self.feed_ids:
                            rss_count += feed["unread"]
            requests.post(api_url, data=json.dumps({"sid": sid, "op": "logOut"}))

            return rss_count

        except:  # noqa e722
            return None


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
