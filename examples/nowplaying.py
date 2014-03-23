# -*- coding: utf-8 -*-

import subprocess
from time import time

class Py3status:
    """
    nowplaying.py

    This module display the current "artist - title" playing in Clementine.

    Last modified: 2014-03-23
    Author: François LASSERRE <choiz@me.com>
    License: GNU GPL http://www.gnu.org/licenses/gpl.html
    """
    def getMetadatas(self):
        """
        Get the current song metadatas (artist - title)
        """
        track_id = subprocess.check_output('qdbus org.mpris.clementine /TrackList org.freedesktop.MediaPlayer.GetCurrentTrack', shell=True)
        metadatas = subprocess.check_output('qdbus org.mpris.clementine /TrackList org.freedesktop.MediaPlayer.GetMetadata '+track_id, shell=True)
        lines = metadatas.split("\n")
        lines = filter(None, lines)

        now_playing = ''

        if len(lines) > 0:

            artist = ''
            title = ''
            internet_radio = 0

            for item in lines:

                if item.find('artist:') != -1:
                    artist = item[8:]

                if item.find('title:') != -1:
                    title = item[7:]

            if (title.find('.wav') != -1) | (title.find('.mp3') != -1):
                title = title[:-4]
            if (title.find("http") != -1):
                title = ""
                internet_radio = 1

            if (len(artist) != 0) & (len(title) != 0):
                now_playing = '♫ '+artist+' - '+title
            elif len(artist) != 0:
                now_playing = '♫ '+artist
            elif len(title) != 0:
                now_playing = '♫ '+title
            elif internet_radio != 0:
                now_playing = '♫ Internet Radio'

        return now_playing

    def setMetadatas(self, json, i3status_config):
        """
        Get the current "artist - title" and return it.
        """
        response = {'full_text': '', 'name': 'track_info'}

        metadata = self.getMetadatas()

        response['full_text'] = metadata
        response['cached_until'] = time()

        return (0, response)
