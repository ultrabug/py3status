# -*- coding: utf-8 -*-
"""
Display Github notifications and issue/pull requests for a repo.

To check notifications a Github `username` and `personal access token` are
required.  You can create a personal access token at
https://github.com/settings/tokens/new?scopes=notifications&description=py3status
The only `scope` needed is `notifications` is selected automatically for you,
which provides readonly access to notifications.

The Github API is rate limited so setting `cache_timeout` too small may cause
issues see https://developer.github.com/v3/#rate-limiting for details

Configuration parameters:
    auth_token: Github personal access token, needed to check notifications
        see above.
        (default None)
    button_action: Button that when clicked opens the Github notification page
        if notifications, else the project page for the repository if there is
        one (otherwise the github home page). Setting to `None` disables.
        (default 3)
    button_refresh: Button that when clicked refreshes module.
        Setting to `None` disables.
        (default 2)
    cache_timeout: How often we refresh this module in seconds
        (default 60)
    format: display format for this module, see Examples below (default None)
    format_notifications: Format of `{notification}` status placeholder.
        (default ' N{notifications_count}')
    notifications: Type of notifications can be `all` for all notifications or
        `repo` to only get notifications for the repo specified.  If repo is
        not provided then all notifications will be checked.
        (default 'all')
    repo: Github repo to check
        (default 'ultrabug/py3status')
    url_api: Change only if using Enterprise Github, example https://github.domain.com/api/v3.
        (default 'https://api.github.com')
    url_base: Change only if using Enterprise Github, example https://github.domain.com.
        (default 'https://github.com')
    username: Github username, needed to check notifications.
        (default None)

Format placeholders:
    {issues} Number of open issues.
    {notifications} Notifications.  If no notifications this will be empty.
    {notifications_count} Number of notifications.  This is also the __Only__
        placeholder available to `format_notifications`.
    {pull_requests} Number of open pull requests
    {repo} short name of the repository being checked. eg py3status
    {repo_full} full name of the repository being checked. eg ultrabug/py3status

Examples:
```
# default formats
github {
    # with username and auth_token, this will be used
    format = '{repo} {issues}/{pull_requests}{notifications}'

    # otherwise, this will be used
    format '{repo} {issues}/{pull_requests}'
}

# set github access credentials
github {
    auth_token = '40_char_hex_access_token'
    username = 'my_username'
}

# just check for any notifications
github {
    auth_token = '40_char_hex_access_token'
    username = 'my_username'
    format = 'Github {notifications_count}'
}
```

@author tobes

SAMPLE OUTPUT
{'full_text': 'py3status 34/24'}

notification
{'full_text': 'py3status 34/24 N3', 'urgent': True}
"""

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


class Py3status:
    """
    """

    # available configuration parameters
    auth_token = None
    button_action = 3
    button_refresh = 2
    cache_timeout = 60
    format = None
    format_notifications = " N{notifications_count}"
    notifications = "all"
    repo = "ultrabug/py3status"
    url_api = "https://api.github.com"
    url_base = "https://github.com"
    username = None

    def post_config_hook(self):
        self.notification_warning = False
        self.repo_warning = False
        self._issues = "?"
        self._pulls = "?"
        self._notify = "?"
        # remove a trailing slash in the urls
        self.url_api = self.url_api.strip("/")
        self.url_base = self.url_base.strip("/")

        # Set format if user has not configured it.
        if not self.format:
            if self.username and self.auth_token:
                # include notifications
                self.format = "{repo} {issues}/{pull_requests}{notifications}"
            else:
                self.format = "{repo} {issues}/{pull_requests}"

    def _github_count(self, url):
        """
        Get counts for requests that return 'total_count' in the json response.
        """
        url = self.url_api + url + "&per_page=1"
        # if we have authentication details use them as we get better
        # rate-limiting.
        if self.username and self.auth_token:
            auth = (self.username, self.auth_token)
        else:
            auth = None
        try:
            info = self.py3.request(url, auth=auth)
        except (self.py3.RequestException):
            return
        if info and info.status_code == 200:
            return int(info.json()["total_count"])
        if info.status_code == 422:
            if not self.repo_warning:
                self.py3.notify_user("Github repo cannot be found.")
                self.repo_warning = True
        return "?"

    def _notifications(self):
        """
        Get the number of unread notifications.
        """
        if not self.username or not self.auth_token:
            if not self.notification_warning:
                self.py3.notify_user(
                    "Github module needs username and "
                    "auth_token to check notifications."
                )
                self.notification_warning = True
            return "?"
        if self.notifications == "all" or not self.repo:
            url = self.url_api + "/notifications"
        else:
            url = self.url_api + "/repos/" + self.repo + "/notifications"
        url += "?per_page=100"
        try:
            info = self.py3.request(url, auth=(self.username, self.auth_token))
        except (self.py3.RequestException):
            return
        if info.status_code == 200:
            links = info.headers.get("Link")

            if not links:
                return len(info.json())

            last_page = 1
            for link in links.split(","):
                if 'rel="last"' in link:
                    last_url = link[link.find("<") + 1 : link.find(">")]
                    parsed = urlparse.urlparse(last_url)
                    last_page = int(urlparse.parse_qs(parsed.query)["page"][0])

            if last_page == 1:
                return len(info.json())
            try:
                last_page_info = self.py3.request(
                    last_url, auth=(self.username, self.auth_token)
                )
            except self.py3.RequestException:
                return

            return len(info.json()) * (last_page - 1) + len(last_page_info.json())

        if info.status_code == 404:
            if not self.repo_warning:
                self.py3.notify_user("Github repo cannot be found.")
                self.repo_warning = True

    def github(self):
        status = {}
        urgent = False
        # issues
        if self.repo and self.py3.format_contains(self.format, "issues"):
            url = "/search/issues?q=state:open+type:issue+repo:" + self.repo
            self._issues = self._github_count(url) or self._issues
        status["issues"] = self._issues
        # pull requests
        if self.repo and self.py3.format_contains(self.format, "pull_requests"):
            url = "/search/issues?q=state:open+type:pr+repo:" + self.repo
            self._pulls = self._github_count(url) or self._pulls
        status["pull_requests"] = self._pulls
        # notifications
        if self.py3.format_contains(self.format, "notifications*"):
            count = self._notifications()
            # if we don't have a notification count, then use the last value
            # that we did have.
            if count is None:
                count = self._notify
            self._notify = count
            if count and count != "?":
                notify = self.py3.safe_format(
                    self.format_notifications, {"notifications_count": count}
                )
                urgent = True
            else:
                notify = ""
            status["notifications"] = notify
            status["notifications_count"] = count
        # repo
        try:
            status["repo"] = self.repo.split("/")[1]
        except IndexError:
            status["repo"] = "Error"
        status["repo_full"] = self.repo

        cached_until = self.py3.time_in(self.cache_timeout)

        return {
            "full_text": self.py3.safe_format(self.format, status),
            "cached_until": cached_until,
            "urgent": urgent,
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_action:
            # open github in browser
            if self._notify and self._notify != "?":
                # open github notifications page
                url = self.url_base + "/notifications"
            else:
                if self.notifications == "all" and not self.repo:
                    # open github.com if there are no unread notifications and no repo
                    url = self.url_base
                else:
                    # open repo page if there are no unread notifications
                    url = self.url_base + "/" + self.repo
            # open url in default browser
            self.py3.command_run("xdg-open {}".format(url))
            self.py3.prevent_refresh()
        elif button != self.button_refresh:
            # only refresh the module if needed
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
