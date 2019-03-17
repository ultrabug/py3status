# -*- coding: utf-8 -*-
"""
Scroll modules.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 1)
    length: specify a length of characters to scroll (default 25)

Format placeholders:
    {output} output

@author farnoy

SAMPLE OUTPUT
[
    {'full_text': 'module 4', 'separator': True},
    {'full_text': 'module 5', 'separator': True},
    {'full_text': 'module 6', 'separator': True},
]
"""

STRING_ERROR = "missing modules"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 1
    length = 25

    class Meta:
        container = True

    def post_config_hook(self):
        if len(self.items) <= 1:
            raise Exception(STRING_ERROR)
        self.format = "{output}"
        self.index = 0

    def _set_scroll(self):
        length = sum(
            len(output["full_text"])
            for item in self.items
            for output in self.py3.get_output(item)
        )

        self.index += 1
        if length <= self.length:
            self.index = 0
        self.index = self.index % length

    def scroll(self):
        self._set_scroll()
        length_position = 0
        last_position = 0

        composite = []
        while length_position < self.length:
            for item in self.items:
                _composite = []
                for output in self.py3.get_output(item):
                    # cut strings
                    start = max(0, self.index - last_position)
                    end = max(0, self.length - length_position)
                    sliced = output["full_text"][start:][:end]
                    # set positions
                    length_position += len(sliced)
                    last_position += len(output["full_text"])
                    output["full_text"] = sliced
                    # disable separators
                    if output["full_text"]:
                        output["separator"] = False
                        _composite.append(output)
                # enable separators
                if _composite:
                    _composite[-1]["separator"] = True
                    _composite[-1].pop("separator_block_width", None)
                composite += _composite

        scroll_data = {"output": self.py3.composite_create(composite)}

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, scroll_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
