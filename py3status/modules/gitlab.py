# -*- coding: utf-8 -*-
"""
Display number of issues, requests and more from a GitLab project.

A token is required. See https://gitlab.com/profile/personal_access_tokens
to make one. Make a name, eg py3status, and enable api in scopes. Save.

Configuration parameters:
    auth_token: specify a personal access token to use (default None)
    button_open: mouse button to open project url (default 1)
    button_refresh: mouse button to refresh this module (default 2)
    cache_timeout: refresh interval for this module (default 900)
    format: display format for this module
        *(default '[{name} ][[{open_issues_count}][\?soft /]'
        '[{open_merge_requests_count}]]')*
    project: specify a project to use (default 'gitlab-org/gitlab-ce')
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    See `sp` below for a full list of supported GitLab placeholders to use.
    Not all of GitLab placeholders will be usable.

    single_project:
        {name}                      project name, eg py3status
        {star_count}                number of stars, eg 2
        {forks_count}               number of forks, eg 3
        {open_issues_count}         number of open issues, eg 4
        {statistics_commit_count}   number of commits, eg 5678
    merge_requests:
        {open_merge_requests_count} number of open merge requests, eg 9
    todos:
        {todos_count}               number of todos, eg 4
    pipelines:
        {pipelines_status}          project status of pipelines, eg success

Notes:
    sp: https://docs.gitlab.com/ee/api/projects.html#get-single-project
    mr: https://docs.gitlab.com/ee/api/merge_requests.html
    td: https://docs.gitlab.com/ee/api/todos.html
    pipe: https://docs.gitlab.com/ee/api/pipelines.html

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Examples:
```
# follow a fictional project, add an icon
gitlab {
    auth_token = 'abcdefghijklmnopq-a4'
    project = 'https://gitlab.com/ultrabug/py3status'

    format = '[\?if=name [\?color=orangered&show ] {name} ]'
    format += '[[{open_issues_count}][\?soft /]'
    format += '[{open_merge_requests_count}][\?soft /]'
    format += '[{pipelines_status}]]'
}
```

@author lasers, Cyril Levis (@cyrinux)

SAMPLE OUTPUT
{'full_text': 'py3status 48/49'}
"""

STRING_ERROR_AUTH = "missing auth_token"


class Py3status:
    """
    """

    # available configuration parameters
    auth_token = None
    button_open = 1
    button_refresh = 2
    cache_timeout = 900
    format = (
        "[{name} ][[{open_issues_count}][\?soft /]" "[{open_merge_requests_count}]]"
    )
    project = "gitlab-org/gitlab-ce"
    thresholds = []

    def post_config_hook(self):
        if not self.auth_token:
            raise Exception(STRING_ERROR_AUTH)
        if not self.project.startswith("http"):
            self.project = "https://gitlab.com/" + self.project

        # make urls
        self.project = self.project.strip("/")
        base_api = self.project.rsplit("/", 2)[0] + "/api/v4/"
        uuid = "/" + "%2F".join(self.project.rsplit("/", 2)[1:])
        single_project = base_api + "projects" + uuid
        merge_requests = "/merge_requests?state=opened&view=simple&per_page=1"
        pipelines = "/pipelines"
        # url stuffs. header, timeout, dict, etc
        self.headers = {"PRIVATE-TOKEN": self.auth_token}
        self.url = {
            "single_project": single_project,
            "merge_requests": single_project + merge_requests,
            "todos": base_api + "todos",
            "pipelines": single_project + pipelines,
        }
        # add statistics to url too?
        if self.py3.format_contains(self.format, "statistics_*"):
            self.url["single_project"] += "/?statistics=true"

        # init placeholders
        self.init = {"thresholds": self.py3.get_color_names_list(self.format)}
        placeholders = self.py3.get_placeholders_list(self.format)
        for x in ["open_merge_requests_count", "todos_count", "pipelines_status"]:
            self.init[x] = x in placeholders
            if self.init[x]:
                placeholders.remove(x)
        self.init["single_project"] = bool(placeholders)

    def _get_data(self, url):
        try:
            return self.py3.request(url, headers=self.headers)
        except self.py3.RequestException:
            return {}

    def gitlab(self):
        gitlab_data = {}

        if self.init["single_project"]:
            data = self._get_data(self.url["single_project"])
            if data:
                gitlab_data.update(self.py3.flatten_dict(data.json(), "_"))

        if self.init["open_merge_requests_count"]:
            data = self._get_data(self.url["merge_requests"])
            if data:
                gitlab_data["open_merge_requests_count"] = data.headers.get("X-Total")

        if self.init["todos_count"]:
            data = self._get_data(self.url["todos"])
            if data:
                gitlab_data["todos_count"] = len(data.json())

        if self.init["pipelines_status"]:
            data = self._get_data(self.url["pipelines"])
            if data:
                gitlab_data["pipelines_status"] = data.json()[0]["status"]

        for x in self.init["thresholds"]:
            if x in gitlab_data:
                self.py3.threshold_get_color(gitlab_data[x], x)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, gitlab_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button == self.button_open:
            self.py3.command_run("xdg-open %s" % self.project)
        if button != self.button_refresh:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
