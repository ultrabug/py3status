# -*- coding: utf-8 -*-
"""
Display the current "artist - title" playing in Clementine.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 5)

Requires:
    clementine:

@author Francois LASSERRE <choiz@me.com>
@license GNU GPL http://www.gnu.org/licenses/gpl.html
"""

from subprocess import check_output

CMD = 'qdbus org.mpris.clementine /TrackList org.freedesktop.MediaPlayer'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5

    def _getMetadatas(self):
        """
        Get the current song metadatas (artist - title)
        """
        track_id = check_output(CMD + '.GetCurrentTrack', shell=True)
        metadatas = check_output(
            CMD + '.GetMetadata {}'.format(track_id.decode()), shell=True
        )
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

    def clementine(self):
        """
        Get the current "artist - title" and return it.
        """
        response = {'full_text': ''}

        response['cached_until'] = self.py3.time_in(self.cache_timeout)
        response['full_text'] = self._getMetadatas()

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
