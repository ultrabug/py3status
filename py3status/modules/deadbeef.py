# -*- coding: utf-8 -*-
"""
Display track currently playing in deadbeef.

Configuration parameters:
    - cache_timeout : how often we refresh usage in seconds (default: 1s)
    - format : see placeholders below
    - delimiter : delimiter character for parsing (default: ¥)

Format of status string placeholders:
    {artist} : artist
    {title} : title
    {elapsed} : elapsed time
    {length} : total length
    {year} : year
    {tracknum} : track number

@author mrt-prodz
"""
from subprocess import check_output
from time import time


class Py3status:
    # available configuration parameters
    cache_timeout = 1
    delimiter = '¥'
    format = '{artist} - {title}'

    # return error occurs
    def _error_response(self, color):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': 'deadbeef: error',
            'color': color
        }
        return response

    # return track currently playing in deadbeef
    def get_status(self, i3s_output_list, i3s_config):
        self.artist = ''
        self.title = ''
        self.length = ''
        self.elapsed = ''
        self.year = ''
        try:
            # get all properties using ¥ as delimiter
            status = check_output(['deadbeef',
                                   '--nowplaying',
                                   '%a' + self.delimiter +
                                   '%t' + self.delimiter +
                                   '%l' + self.delimiter +
                                   '%e' + self.delimiter +
                                   '%y' + self.delimiter +
                                   '%n'])
            # check if we have music currently  playing
            if 'nothing' in status:
                response = {
                    'cached_until': time() + self.cache_timeout,
                    'full_text': ''
                }
                return response
            # split properties using special delimiter
            parts = status.split(self.delimiter)
            if len(parts) == 6:
                self.artist = parts[0]
                self.title = parts[1]
                self.length = parts[2]
                self.elapsed = parts[3]
                self.year = parts[4]
                self.tracknum = parts[5]
            else:
                return self._error_response(i3s_config['color_bad'])

            response = {
                'cached_until': time() + self.cache_timeout,
                'full_text': self.format.format(artist=self.artist,
                                                title=self.title,
                                                length=self.length,
                                                elapsed=self.elapsed,
                                                year=self.year,
                                                tracknum=self.tracknum)
            }
            return response
        except:
            return self._error_response(i3s_config['color_bad'])

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_degraded': '#00FFFF',
        'color_bad': '#FF0000'
    }
    print(x.get_status([], config))
