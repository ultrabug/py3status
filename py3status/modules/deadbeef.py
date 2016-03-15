# -*- coding: utf-8 -*-
"""
Display track currently playing in deadbeef.

Configuration parameters:
    cache_timeout: how often we refresh usage in seconds (default: 1s)
    format: see placeholders below
    delimiter: delimiter character for parsing (default: ¥)

Format of status string placeholders:
    {artist} artist
    {title} title
    {elapsed} elapsed time
    {length} total length
    {year} year
    {tracknum} track number


Requires:
        deadbeef:

@author mrt-prodz
"""
from subprocess import check_output, CalledProcessError
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

    # return empty response
    def _empty_response(self):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }
        return response

    # return track currently playing in deadbeef
    def get_status(self, i3s_output_list, i3s_config):
        try:
            # check if we have deadbeef running
            check_output(['pidof', 'deadbeef'])
        except CalledProcessError:
            return self._empty_response()

        try:
            # get all properties using ¥ as delimiter
            status = check_output(['deadbeef',
                                   '--nowplaying',
                                   self.delimiter.join(['%a',
                                                        '%t',
                                                        '%l',
                                                        '%e',
                                                        '%y',
                                                        '%n'])])

            if status == 'nothing':
                return self._empty_response()

            # split properties using special delimiter
            parts = status.split(self.delimiter)
            if len(parts) == 6:
                artist, title, length, elapsed, year, tracknum = parts
            else:
                return self._error_response(i3s_config['color_bad'])

            response = {
                'cached_until': time() + self.cache_timeout,
                'full_text': self.format.format(artist=artist,
                                                title=title,
                                                length=length,
                                                elapsed=elapsed,
                                                year=year,
                                                tracknum=tracknum)
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
