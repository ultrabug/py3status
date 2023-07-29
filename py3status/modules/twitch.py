"""
Display if a Twitch channel is currently streaming or not.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 60)
    client_id: Your client id. Create your own key at https://dev.twitch.tv
        (default None)
    client_secret: Your client secret.
        (default None)
    format: Display format when online
        (default "{display_name} is live!")
    format_offline: Display format when offline
        (default "{display_name} is offline.")
    format_tag: Tag formatting
        (default "{name}")
    locales: List of locales to try for tag translations, eg. ["cs-cz", "en-uk", "en-us"]. If none is specified, auto-detect from environment, with a fallback to "en-us".
        (default [])
    stream_name: name of streamer(twitch.tv/<stream_name>)
        (default None)
    tag_delimiter: string to write between tags
        (default " ")
    trace: enable trace level debugging
        (default False)

Stream format placeholders:
    {display_name} User's display name., eg Ultrabug
    {is_streaming} (bool) True if streaming, fields prefixed with stream_ are available.
    {tags} List of tags
    {user_id} User's id
    {user_login} User's login name, eg xisumavoid
    {user_display_name} (same as {display_name})
    {user_type} "staff", "admin", "global_mod", or ""
    {user_broadcaster_type} "partner", "affiliate", or "".
    {user_description} User's channel description.
    {user_profile_image_url} URL of the user's profile image.
    {user_offline_image_url} URL of the user's offline image.
    {user_view_count} Total number of views of the user's channel.
    {user_created_at} Date when the user was created.
    {stream_id} Stream ID.
    {stream_game_id} ID of the game being played on the stream.
    {stream_game_name} Name of the game being played.
    {stream_title} Stream title.
    {stream_viewer_count} Number of viewers watching the stream at the time of last update.
    {stream_started_at} Stream start UTC timestamp.
    {stream_language} Stream language. A language value is either the ISO 639-1 two-letter code or “other”.
    {stream_thumbnail_url} Thumbnail URL of the stream. All image URLs have variable width and height. You can replace {width} and {height} with any values to get that size image
    {stream_is_mature} Indicates if the broadcaster has specified their channel contains mature content that may be inappropriate for younger audiences.
    {stream_runtime} (string) Stream runtime as a human readable, non-localized string. eg "3h 5m"
    {stream_runtime_seconds} (int) Stream runtime in seconds.

Tag format placeholders: (see locales)
    {name} The tag name
    {desc} The tag description

Color options:
    color_bad: Stream offline
    color_good: Stream is live

Client ID:
    Example settings when creating your app at https://dev.twitch.tv

    Name: <your_name>_py3status
    OAuth Redirect URI: https://localhost
    Application Category: Application Integration


@author Alex Caswell horatioesf@virginmedia.com
@author Julian Picht julian.picht@gmail.com
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'exotic_bug is live!'}

offline
{'color': '#FF0000', 'full_text': 'exotic_bug is offline!'}
"""

import datetime
import time

STRING_MISSING = "missing {}"


def time_since(s):
    ts = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timestamp()
    seconds = int(datetime.datetime.utcnow().timestamp() - ts)
    if seconds > 3600:
        return "%dh %dm" % (seconds / 3600, (seconds % 3600) / 60), seconds
    if seconds > 60:
        return "%dm" % (seconds / 60), seconds
    return "0m", seconds


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 60
    client_id = None
    client_secret = None
    format = "{display_name} is live!"
    format_offline = "{display_name} is offline."
    format_tag = "{name}"
    locales = []
    stream_name = None
    tag_delimiter = " "
    trace = False

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

    def _trace(self, msg):
        if not self.trace:
            return
        self.py3.log(msg, self.py3.LOG_INFO)

    def _refresh_token(self):
        if self._token and self._token["expires"] > time.time():
            return

        self._trace("refreshing twitch oauth token")
        auth_endpoint = "https://id.twitch.tv/oauth2/token"
        auth_request = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        try:
            response = self.py3.request(auth_endpoint, data=auth_request)
        except self.py3.RequestException:
            return {}

        data = response.json()
        if not data:
            data = vars(response)
            error = data.get("_error_message")
            if error:
                self.py3.error("{} {}".format(error, data["_status_code"]))

        self._token = data
        self._token["expires"] = time.time() + self._token["expires_in"] - 60
        self.py3.storage_set("oauth_token", self._token)

    def _headers(self):
        self._refresh_token()
        return {
            "Authorization": "Bearer " + self._token["access_token"],
            "Client-ID": self.client_id,
        }

    def post_config_hook(self):
        for config_name in ["client_id", "client_secret", "stream_name"]:
            if not getattr(self, config_name, None):
                raise Exception(STRING_MISSING.format(config_name))

        base_api = "https://api.twitch.tv/helix/"
        self.url = {
            "users": base_api + f"users/?login={self.stream_name}",
            "streams": base_api + f"streams/?user_login={self.stream_name}",
            "tags": base_api + "streams/tags",
        }

        self.user = {}
        self._token = self.py3.storage_get("oauth_token")

        if self.locales is False:
            return

        have_tags = (
            self.py3.format_contains(self.format, "tags")
            or
            # it doesn't make any sense here... but we'll check
            self.py3.format_contains(self.format_offline, "tags")
        )

        if not have_tags:
            self.locales = False
            return

        if not isinstance(self.locales, list):
            self.locales = [x for x in [str(self.locales)] if x]

        if len(self.locales) == 0:
            try:
                import locale

                self.locales = [locale.getdefaultlocale()[0].lower().replace("_", "-")]
            except (ModuleNotFoundError, IndexError):
                pass

        if "en-us" not in self.locales:
            self.locales.append("en-us")

    def _get_twitch_data(self, url, first=True):
        try:
            response = self.py3.request(url, headers=self._headers())
        except self.py3.RequestException as e:
            self.py3.error(f"get({url}): exception={e}")
            return {}
        data = response.json()
        if not data:
            data = vars(response)
            error = data.get("_error_message")
            if error:
                self.py3.error("{} {}".format(error, data["_status_code"]))

        if first:
            if len(data["data"]) > 0:
                return data["data"][0]
            return {}

        cursor = False
        if "pagination" in data and "cursor" in data["pagination"]:
            cursor = data["pagination"]["cursor"]

        return data["data"], cursor

    def _get_tags(self, user_id, cursor=None):
        if self.locales is False:
            return self.py3.composite_create([])

        url = self.url["tags"] + f"?broadcaster_id={user_id}"

        if cursor is not None:
            url = f"{url}&after={cursor}"

        self._trace(f"fetching tags, page={cursor}")

        tags = []
        page, next_cursor = self._get_twitch_data(url, first=False)
        if page:
            for tag in page:
                tag_data = {}
                for loc in self.locales:
                    if loc in tag["localization_names"] and "name" not in tag_data:
                        tag_data["name"] = tag["localization_names"][loc]
                    if loc in tag["localization_descriptions"] and "desc" not in tag_data:
                        tag_data["desc"] = tag["localization_descriptions"][loc]
                if tag_data:
                    tags.append(self.py3.safe_format(self.format_tag, tag_data))

        if next_cursor:
            tags.append(*self._get_tags(user_id, next_cursor))

        return tags

    def twitch(self):
        if not self.user:
            self._trace("fetching user")
            self.user = self._get_twitch_data(self.url["users"])

        twitch_data = {
            "user": self.user,
            # ensure display name is still there, deprecate+remove later?
            "display_name": self.user["display_name"],
        }
        current_format = ""
        color = None

        self._trace("fetching stream data")
        stream = self._get_twitch_data(self.url["streams"])
        if stream and "type" in stream and stream["type"] == "live":
            # this is always "live" if the stream is healthy
            del stream["type"]
            # remove useless UUIDs
            del stream["tag_ids"]
            # remove redundant data
            del stream["user_id"]
            del stream["user_login"]
            del stream["user_name"]

            # calculate runtime and  update data dict
            stream["runtime"], stream["runtime_seconds"] = time_since(stream["started_at"])
            twitch_data["stream"] = stream
            twitch_data["is_streaming"] = True

            color = self.py3.COLOR_GOOD
            current_format = self.format
        else:
            twitch_data["is_streaming"] = False
            color = self.py3.COLOR_BAD
            current_format = self.format_offline

        twitch_data = self.py3.flatten_dict(twitch_data, delimiter="_")
        twitch_data["tags"] = self.py3.composite_join(
            self.tag_delimiter, self._get_tags(self.user["id"])
        )

        self._trace("fields available: {}".format(list(twitch_data.keys())))

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
    from os import getenv

    from py3status.module_test import module_test

    config = {
        "client_id": getenv("TWITCH_CLIENT_ID"),
        "client_secret": getenv("TWITCH_CLIENT_SECRET"),
        "stream_name": "xisumavoid",
        "format": "{display_name} is playing {stream_game_name} for {stream_runtime} with title '{stream_title}'\n\tlanguage: {stream_language}\n\tviewers: {stream_viewer_count}\n\ttags:\n{tags}",
        "format_tag": "\t\t{name} -> {desc}",
        "tag_delimiter": "\n",
        "locales": "invalid",
        "trace": True,
    }

    module_test(Py3status, config)
