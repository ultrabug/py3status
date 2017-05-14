# -*- coding: utf-8 -*-
"""
Display track currently playing in Quod Libet.

Configuration parameters:
    cache_timeout: how often we refresh usage in seconds (default: 1s)
    format: Output format (default: "{track}")
    quodlibet_format: Quod Libet tag pattern to use for song. See
        https://quodlibet.readthedocs.io/en/latest/guide/tags/patterns.html
        for Quod Libet's documentation on them. (default: "<artist~title>")
    quodlibet_directory: Directory of Quod Libet (default: "~/.quodlibet")

Format of status string placeholders:
    {track} Current song, formatted by quodlibet_format


Requires:
        quodlibet:
"""
from subprocess import check_output
from time import time
import os.path


class Py3status:
    # available configuration parameters
    cache_timeout = 1
    format = '{track}'
    quodlibet_format = '<artist~title>'
    quodlibet_directory = '~/.quodlibet'

    # return error occurs
    def _error_response(self, color):
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': 'quodlibet: error',
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

    # Return track currently playing in quodlibet
    def get_status(self, i3s_output_list, i3s_config):
        expanded_directory = os.path.expanduser(self.quodlibet_directory)
        current_file = os.path.join(expanded_directory, 'current')
        # Test if Quod Libet is running
        if not os.path.exists(current_file):
            return self._empty_response()

        try:
            # Get track using Quod Libet's formatting mechanism
            track = check_output(['quodlibet',
                                  '--print-playing',
                                  self.quodlibet_format])

            response = {
                'cached_until': time() + self.cache_timeout,
                'full_text': self.format.format(track=track)
            }
            return response
        except:
            return self._error_response(i3s_config['color_bad'])

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    config = {
        'color_good': '#00FF00',
        'color_degraded': '#00FFFF',
        'color_bad': '#FF0000'
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
