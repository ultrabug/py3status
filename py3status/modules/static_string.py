"""
Display static text.

Configuration parameters:
    format: display format for this module (default 'Hello, world!')

@author frimdo ztracenastopa@centrum.cz

SAMPLE OUTPUT
{'full_text': 'Hello, world!'}
"""


class Py3status:
    """
    """

    # available configuration parameters
    format = "Hello, world!"

    def static_string(self):
        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
