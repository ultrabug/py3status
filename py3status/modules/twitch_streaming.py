"""
Checks if a Twitch streamer is online.

Checks if a streamer is online using the Twitch Kraken API to see
if a channel is currently streaming or not.

Configuration parameters
    cache_timeout: how often we refresh this module in seconds
        (default 10)
    format: Display format when online
        (default "{stream_name} is live!")
    format_offline: Display format when offline
        (default "{stream_name} is offline.")
    format_invalid: Display format when streamer does not exist
        (default "{stream_name} does not exist!")
    stream_name: name of streamer(twitch.tv/<stream_name>)
        (default None)

Format of status string placeholders
    {stream_name}:  name of the streamer

@author Alex Caswell horatioesf@virginmedia.com
@license BSD
"""

import requests


class Py3status:
    # available configuration parameters
    # can be customized in i3status.conf
    cache_timeout = 10
    format = "{stream_name} is live!"
    format_offline = "{stream_name} is offline."
    format_invalid = "{stream_name} does not exist!"
    stream_name = None

    def __init__(self):
        self._display_name = None

    def _get_display_name(self):
        url = 'https://api.twitch.tv/kraken/users/' + self.stream_name
        display_name_request = requests.get(url)
        self._display_name = display_name_request.json().get('display_name')

    def is_streaming(self):
        if self.stream_name is None:
            return {
                'full_text': 'stream_name missing',
                'cached_until': self.py3.CACHE_FOREVER
            }

        i3s_config = self.py3.i3s_config()

        r = requests.get('https://api.twitch.tv/kraken/streams/' + self.stream_name)
        if not self._display_name:
            self._get_display_name()
        if 'error' in r.json():
            colour = i3s_config['color_bad']
            full_text = self.format_invalid.format(stream_name=self.stream_name)
        elif r.json().get('stream') is None:
            colour = i3s_config['color_bad']
            full_text = self.format_offline.format(stream_name=self._display_name)
        elif r.json().get('stream') is not None:
            colour = i3s_config['color_good']
            full_text = self.format.format(stream_name=self._display_name)
        else:
            colour = i3s_config['color_bad']
            full_text = "An unknown error has occurred."

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text,
            'color': colour
        }
        return response

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        'stream_name': 'moo'
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
