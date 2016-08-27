# -*- coding: utf-8 -*-
"""
Display current sound volume using pamixer.

Configuration parameters:
    threshold_bad: Volume above which the color is set to bad
        (default: 90)
    threshold_degraded: Volume above which the color is set to degraded
        (default: 50)
    format: format string
        (default: "♪{volume:3d}%")
    format_mute: format string when sound is muted
        (default: "♪ -- ")

Format status string parameters:
    {volume} the volume percent

Color options:
    color_bad: Volume above threshold_bad
    color_degraded: Volume above threshold_degraded
    color_good: Volume below to threshold_degraded
"""

# import your useful libs here
import subprocess


class Py3status:
    def __init__(self):
        self.cache_timeout = 10
        self.threshold_degraded = 50
        self.threshold_bad = 90
        self.format = "♪{volume:3d}%"
        self.format_mute = "♪ -- "
        pass

    def volume(self):
        """
        This method will return an empty text message
        so it will NOT be displayed on your i3bar.

        If you want something displayed you should write something
        in the 'full_text' key of your response.

        See the i3bar protocol spec for more information:
        http://i3wm.org/docs/i3bar-protocol.html
        """
        response = {
            'cached_until': self.py3.time_in(seconds=self.cache_timeout),
            'full_text': ''
        }
        volume = int(subprocess.check_output(["pamixer", "--get-volume"]).decode('utf-8'))
        mute = (subprocess.run(["pamixer", "--get-mute"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
        if volume < self.threshold_degraded:
            response['color'] = self.py3.COLOR_GOOD
        elif volume < self.threshold_bad:
            response['color'] = self.py3.COLOR_DEGRADED
        else:
            response['color'] = self.py3.COLOR_BAD
        if mute:
            format_string = self.format_mute
        else:
            format_string = self.format
        response['full_text'] = self.py3.safe_format(format_string,
                {'volume': volume})

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
