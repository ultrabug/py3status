# -*- coding: utf-8 -*-
"""
This module displays the current "artist - title" playing in Clementine.

Last modified: 2014-03-23
Author: Francois LASSERRE <choiz@me.com>
License: GNU GPL http://www.gnu.org/licenses/gpl.html
"""

from time import time
from subprocess import check_output


class Py3status:

    # available configuration parameters
    cache_timeout = 0

    def _getMetadatas(self):
        """
        Get the current song metadatas (artist - title)
        """
        track_id = check_output('qdbus org.mpris.clementine /TrackList org.freedesktop.MediaPlayer.GetCurrentTrack', shell=True)
        metadatas = check_output('qdbus org.mpris.clementine /TrackList org.freedesktop.MediaPlayer.GetMetadata {}'.format(track_id.decode()), shell=True)
        lines = metadatas.decode('utf-8').split('\n')
        lines = filter(None, lines)

        now_playing = ''

        if lines:
            artist = ''
            title = ''
            internet_radio = False

            for item in lines:
                if item.find('artist:') != -1:
                    artist = item[8:]
                if item.find('title:') != -1:
                    title = item[7:]

            if title.find('.wav') != -1 or title.find('.mp3') != -1:
                title = title[:-4]
            if title.find('http') != -1:
                title = ''
                internet_radio = True

            if artist and title:
                now_playing = '♫ {} - {}'.format(artist, title)
            elif artist:
                now_playing = '♫ {}'.format(artist)
            elif title:
                now_playing = '♫ {}'.format(title)
            elif internet_radio:
                now_playing = '♫ Internet Radio'

        return now_playing

    def clementine(self, i3s_output_list, i3s_config):
        """
        Get the current "artist - title" and return it.
        """
        response = {'full_text': ''}

        response['cached_until'] = time() + self.cache_timeout
        response['full_text'] = self._getMetadatas()

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.clementine([], {}))
        sleep(1)
