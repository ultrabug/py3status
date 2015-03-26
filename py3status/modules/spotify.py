# -*- coding: utf-8 -*-
"""
This module displays the current "artist - title" playing in Spotify.

Last modified: 2015-03-26
Author: Pierre Guilbert LASSERRE <pierre@1000mercis.com>
License: GNU GPL http://www.gnu.org/licenses/gpl.html
"""

from time import time
from subprocess import check_output
import dbus, dbus.proxies

class Py3status:

    # available configuration parameters
    cache_timeout = 0

    def getText(self):
        """
        Get the current song metadatas (artist - title)
        """
        
        bus = dbus.SessionBus()

        try:
            self.__bus  = bus.get_object('com.spotify.qt', '/')
            self.player = dbus.Interface(self.__bus, 'org.freedesktop.MediaPlayer2')

            title = self.player.GetMetadata().get('xesam:title')
            artist = self.player.GetMetadata().get('xesam:artist')[0]
            album = self.player.GetMetadata().get('xesam:album')
            return title + " by " + artist 
        except Exception:
            return "Spotify not running"

    def spotify(self, i3s_output_list, i3s_config):
        """
        Get the current "artist - title" and return it.
        """
        response = {'full_text': ''}

        response['cached_until'] = time() + self.cache_timeout
        response['full_text'] = self.getText() or 'py3status module not working as expected'

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
