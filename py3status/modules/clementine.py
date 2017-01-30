# -*- coding: utf-8 -*-
"""
Display song currently playing in Clementine.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module (default '♫ {current}')
    string_unavailable: unavailable format (default 'clementine: N/A')

Format placeholders:
    {current} currently playing

Requires:
    clementine:

@author Francois LASSERRE <choiz@me.com>
@license GNU GPL http://www.gnu.org/licenses/gpl.html
"""

CMD = 'qdbus org.mpris.clementine /TrackList org.freedesktop.MediaPlayer'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = u'♫ {current}'
    string_unavailable = 'clementine: N/A'

    def clementine(self):
        """
        Get current song metadata: "artist - title"
        """
        artist = lines = now_playing = title = ''
        internet_radio = False
        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        try:
            track_id = self.py3.command_output(CMD + '.GetCurrentTrack')
            metadata = self.py3.command_output(CMD + '.GetMetadata {}'.format(track_id))
            lines = filter(None, metadata.splitlines())
        except:
            response['color'] = self.py3.COLOR_BAD
            response['full_text'] = self.string_unavailable
        else:
            if lines:
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
                    now_playing = '{} - {}'.format(artist, title)
                elif artist:
                    now_playing = artist
                elif title:
                    now_playing = title
                elif internet_radio:
                    now_playing = 'Internet Radio'

                response['full_text'] = self.py3.safe_format(
                    self.format, {'current': now_playing}).strip()

        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
