# -*- coding: utf-8 -*-
"""
Display information about the current song playing on Spotify.

Configuration parameters:
    - cache_timeout : how often to update the bar
    - format : see placeholders below

Format of status string placeholders:
    {album} - album name
    {artist} - artiste name (first one)
    {time} - time duration of the song
    {title} - name of the song

i3status.conf example:

spotify {
    format = "{title} by {artist} -> {time}"
}

@author Pierre Guilbert <pierre@1000mercis.com>
"""

from datetime import timedelta
from time import time
import dbus


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = '{artist} : {title}'

    def getText(self):
        """
        Get the current song metadatas (artist - title)
        """
        bus = dbus.SessionBus()
        try:
            self.__bus = bus.get_object('com.spotify.qt', '/')
            self.player = dbus.Interface(
                self.__bus, 'org.freedesktop.MediaPlayer2')

            album = self.player.GetMetadata().get('xesam:album')
            artist = self.player.GetMetadata().get('xesam:artist')[0]
            microtime = self.player.GetMetadata().get('mpris:length')
            rtime = str(timedelta(microseconds=microtime))
            title = self.player.GetMetadata().get('xesam:title')

            return self.format.format(title=title,
                                      artist=artist, album=album, time=rtime)
        except Exception:
            return 'Spotify not running'

    def spotify(self, i3s_output_list, i3s_config):
        """
        Get the current "artist - title" and return it.
        """
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': self.getText()
        }
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.spotify([], config))
        sleep(1)
