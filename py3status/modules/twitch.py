# -*- coding: utf-8 -*-
"""
Display if a Twitch channel is currently streaming or not.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 60)
    client_id: Your client id. Create your own key at https://dev.twitch.tv
        (default None)
    format: Display format when online
        (default "{display_name} is live!")
    format_offline: Display format when offline
        (default "{display_name} is offline.")
    stream_name: name of streamer(twitch.tv/<stream_name>)
        (default None)

Format placeholders:
    {display_name} streamer display name, eg Ultrabug

Color options:
    color_bad: Stream offline
    color_good: Stream is live

Client ID:
    Example settings when creating your app at https://dev.twitch.tv

    Name: <your_name>_py3status
    OAuth Redirect URI: https://localhost
    Application Category: Application Integration


@author Alex Caswell horatioesf@virginmedia.com
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'exotic_bug is live!'}

offline
{'color': '#FF0000', 'full_text': 'exotic_bug is offline!'}
"""

STRING_MISSING = "missing {}"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 60
    client_id = None
    format = "{display_name} is live!"
    format_offline = "{display_name} is offline."
    stream_name = None

    class Meta:
        deprecated = {
            "remove": [{"param": "format_invalid", "msg": "obsolete"}],
            "rename_placeholder": [
                {
                    "placeholder": "stream_name",
                    "new": "display_name",
                    "format_strings": ["format"],
                }
            ],
        }

    def post_config_hook(self):
        for config_name in ["client_id", "stream_name"]:
            if not getattr(self, config_name, None):
                raise Exception(STRING_MISSING.format(config_name))

        self.headers = {"Client-ID": self.client_id}
        base_api = "https://api.twitch.tv/kraken/"
        self.url = {
            "users": base_api + "users/{}".format(self.stream_name),
            "streams": base_api + "streams/{}".format(self.stream_name),
        }
        self.users = {}

    def _get_twitch_data(self, url):
        try:
            response = self.py3.request(url, headers=self.headers)
        except self.py3.RequestException:
            return {}
        data = response.json()
        if not data:
            data = vars(response)
            error = data.get("_error_message")
            if error:
                self.py3.error("{} {}".format(error, data["_status_code"]))
        return data

    def twitch(self):
        twitch_data = self.users
        current_format = ""
        color = None

        if not twitch_data:
            self.users = self._get_twitch_data(self.url["users"])
            twitch_data.update(self.users)

        streams = self._get_twitch_data(self.url["streams"])
        if streams:
            twitch_data.update(streams)
            if twitch_data["stream"]:
                color = self.py3.COLOR_GOOD
                current_format = self.format
            else:
                color = self.py3.COLOR_BAD
                current_format = self.format_offline

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(current_format, twitch_data),
        }
        if color:
            response["color"] = color
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
