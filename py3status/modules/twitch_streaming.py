"""
Display status on a given Twitch streamer.

Checks if a streamer is online using the Twitch Kraken API to see
if a channel is currently streaming or not.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 10)
    format: Display format when online
        (default "{stream_name} is live!")
    format_invalid: Display format when streamer does not exist
        (default "{stream_name} does not exist!")
    format_offline: Display format when offline
        (default "{stream_name} is offline.")
    stream_name: name of streamer(twitch.tv/<stream_name>)
        (default None)

Format placeholders:
    {stream_name}:  name of the streamer

Color options:
    color_bad: Stream offline or error
    color_good: Stream is live

@author Alex Caswell horatioesf@virginmedia.com
@license BSD

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': 'exotic_bug is live!'}

offline
{'color': '#FF0000', 'full_text': 'exotic_bug is offline!'}
"""

import requests


class Py3status:
    # available configuration parameters
    # can be customized in i3status.conf
    cache_timeout = 10
    format = "{stream_name} is live!"
    format_invalid = "{stream_name} does not exist!"
    format_offline = "{stream_name} is offline."
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

        r = requests.get('https://api.twitch.tv/kraken/streams/' + self.stream_name)
        if not self._display_name:
            self._get_display_name()
        if 'error' in r.json():
            colour = self.py3.COLOR_BAD
            format = self.format_invalid
            stream_name = self.stream_name
        elif r.json().get('stream') is None:
            colour = self.py3.COLOR_BAD
            format = self.format_offline
            stream_name = self._display_name
        elif r.json().get('stream') is not None:
            colour = self.py3.COLOR_GOOD
            format = self.format
            stream_name = self._display_name
        else:
            colour = self.py3.COLOR_BAD
            format = "An unknown error has occurred."
            stream_name = None

        full_text = self.py3.safe_format(format, {'stream_name': stream_name})

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
