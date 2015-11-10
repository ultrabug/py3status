# -*- coding: utf-8 -*-
"""
Display information about the current song playing on Spotify.

Configuration parameters:
    - cache_timeout : how often to update the bar
    - format : see placeholders below
    - color_playing : text color when song is playing, defaults to color_good
    - color_paused : text color when song is stopped or paused, defaults to color_degraded
    - color_offline : text color when spotify is not running, defaults to color_bad

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
    color_playing = None
    color_paused = None
    color_offline = None
    format = '{artist} : {title}'

    def getText(self, i3s_config):
        """
        Get the current song metadatas (artist - title)
        """
        bus = dbus.SessionBus()
        try:
            self.__bus = bus.get_object('org.mpris.MediaPlayer2.spotify',
                                        '/org/mpris/MediaPlayer2')
            self.player = dbus.Interface(
                self.__bus, 'org.freedesktop.DBus.Properties')

            metadata = self.player.Get('org.mpris.MediaPlayer2.Player',
                                       'Metadata')
            album = metadata.get('xesam:album')
            artist = metadata.get('xesam:artist')[0]
            microtime = metadata.get('mpris:length')
            rtime = str(timedelta(microseconds=microtime))
            title = metadata.get('xesam:title')

            playback_status = self.player.Get('org.mpris.MediaPlayer2.Player',
                                              'PlaybackStatus')
            if playback_status.strip() == 'Playing':
                color = self.color_playing or i3s_config['color_good']
            else:
                color = self.color_paused or i3s_config['color_degraded']

            return (
                self.format.format(title=title, artist=artist, album=album,
                                   time=rtime),
                color
            )
        except Exception:
            return (
                'Spotify not running',
                self.color_offline or i3s_config['color_bad']
            )

    def spotify(self, i3s_output_list, i3s_config):
        """
        Get the current "artist - title" and return it.
        """
        (text, color) = self.getText(i3s_config)
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': text,
            'color': color
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
        'color_degraded': '#FFFF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.spotify([], config))
        sleep(1)
