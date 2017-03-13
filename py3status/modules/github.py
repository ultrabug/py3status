# -*- coding: utf-8 -*-
"""
Display Github notifications and issue/pull requests for a repo.

To check notifications a Github `username` and `personal access token` are
required.  You can create a personal access token at
https://github.com/settings/tokens The only `scope` needed is `notifications`,
which provides readonly access to notifications.

The Github API is rate limited so setting `cache_timeout` too small may cause
issues see https://developer.github.com/v3/#rate-limiting for details

Configuration parameters:
    auth_token: Github personal access token, needed to check notifications
        see above.
        (default None)
    button_action: Button that when clicked opens the Github notification page
        if notifications, else the project page for the repository if there is
        one (otherwise the github home page). Setting to `0` disables.
        (default 3)
    cache_timeout: How often we refresh this module in seconds
        (default 60)
    format: Format of output
        *(default '{repo} {issues}/{pull_requests}{notifications}'
        if username and auth_token provided else
        '{repo} {issues}/{pull_requests}')*
    format_notifications: Format of `{notification}` status placeholder.
        (default ' N{notifications_count}')
    notifications: Type of notifications can be `all` for all notifications or
        `repo` to only get notifications for the repo specified.  If repo is
        not provided then all notifications will be checked.
        (default 'all')
    repo: Github repo to check
        (default 'ultrabug/py3status')
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

GITHUB_API_URL = 'https://api.github.com'
GITHUB_URL = 'https://github.com/'


class Py3status:
    auth_token = None
    button_action = 3
    cache_timeout = 60
    format = None
    format_notifications = ' N{notifications_count}'
    notifications = 'all'
    repo = 'ultrabug/py3status'
    username = None

    def __init__(self):
        self.first = True
        self.notification_warning = False
        self.repo_warning = False
        self._issues = '?'
        self._pulls = '?'
        self._notify = '?'

    def _init(self):
        # Set format if user has not configured it.
        if not self.format:
            if self.username and self.auth_token:
                # include notifications
                self.format = '{repo} {issues}/{pull_requests}{notifications}'
            else:
                self.format = '{repo} {issues}/{pull_requests}'

    def _github_count(self, url):
        '''
        Get counts for requests that return 'total_count' in the json response.
        '''
        if self.first:
            return '?'
        url = GITHUB_API_URL + url + '&per_page=1'
        # if we have authentication details use them as we get better
        # rate-limiting.
        if self.username and self.auth_token:
            auth = (self.username, self.auth_token)
        else:
            auth = None
        try:
            info = self.py3.request(url, timeout=10, auth=auth)
        except (self.py3.RequestException):
            return
        if info and info.status_code == 200:
            return(int(info.json()['total_count']))
        if info.status_code == 422:
            if not self.repo_warning:
                self.py3.notify_user('Github repo cannot be found.')
                self.repo_warning = True
        return '?'

    def _notifications(self):
        '''
        Get the number of unread notifications.
        '''
        if not self.username or not self.auth_token:
            if not self.notification_warning:
                self.py3.notify_user('Github module needs username and '
                                     'auth_token to check notifications.')
                self.notification_warning = True
            return '?'
        if self.first:
            return '?'
        if self.notifications == 'all' or not self.repo:
            url = GITHUB_API_URL + '/notifications'
        else:
            url = GITHUB_API_URL + '/repos/' + self.repo + '/notifications'
        url += '?per_page=100'
        try:
            info = self.py3.request(url, timeout=10,
                                    auth=(self.username, self.auth_token))
        except (self.py3.RequestException):
            return
        if info.status_code == 200:
            return len(info.json())
        if info.status_code == 404:
            if not self.repo_warning:
                self.py3.notify_user('Github repo cannot be found.')
                self.repo_warning = True

    def github(self):
        if self.first:
            self._init()
        status = {}
        urgent = False
        # issues
        if self.repo and self.py3.format_contains(self.format, 'issues'):
            url = '/search/issues?q=state:open+type:issue+repo:' + self.repo
            self._issues = self._github_count(url) or self._issues
        status['issues'] = self._issues
        # pull requests
        if self.repo and self.py3.format_contains(self.format, 'pull_requests'):
            url = '/search/issues?q=state:open+type:pr+repo:' + self.repo
            self._pulls = self._github_count(url) or self._pulls
        status['pull_requests'] = self._pulls
        # notifications
        if (self.py3.format_contains(self.format, 'notifications') or
                self.py3.format_contains(self.format, 'notifications_count')):
            count = self._notifications()
            # if we don't have a notification count, then use the last value
            # that we did have.
            if count is None:
                count = self._notify
            self._notify = count
            if count and count != '?':
                notify = self.py3.safe_format(
                    self.format_notifications,
                    {'notifications_count': count})
                urgent = True
            else:
                notify = ''
            status['notifications'] = notify
            status['notifications_count'] = count
        # repo
        try:
            status['repo'] = self.repo.split('/')[1]
        except IndexError:
            status['repo'] = 'Error'
        status['repo_full'] = self.repo

        if self.first:
            cached_until = 0
            self.first = False
        else:
            cached_until = self.py3.time_in(self.cache_timeout)

        return {
            'full_text': self.py3.safe_format(self.format, status),
            'cached_until': cached_until,
            'urgent': urgent
        }

    def on_click(self, event):
        button = event['button']
        if self.button_action and self.button_action == button:
            if self._notify and self._notify != '?':
                # open github notifications page
                url = GITHUB_URL + 'notifications'
            else:
                if self.notifications == 'all' and not self.repo:
                    # open github.com if there are no unread notifications and no repo
                    url = GITHUB_URL
                else:
                    # open repo page if there are no unread notifications
                    url = GITHUB_URL + self.repo
            # open url in default browser
            self.py3.command_run('xdg-open {}'.format(url))
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
