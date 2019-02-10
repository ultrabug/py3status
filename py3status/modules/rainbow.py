# -*- coding: utf-8 -*-
"""
Add color cycling fun to your i3bar.

This is the most pointless yet most exciting module you can imagine.

It allows color cycling of modules. Imagine the joy of having the current time
change through the colors of the rainbow.

If you were completely insane you could also use it to implement the i3bar
equivalent of the <blink> tag and cause yourself endless headaches and the
desire to vomit.

The color for the contained module(s) is changed and cycles through your chosen
gradient by default this is the colors of the rainbow.  This module will
increase the amount of updates that py3status needs to do so should be used
sparingly.

Configuration parameters:
    cycle_time: How often we change this color in seconds
        (default 1)
    force: If True then the color will always be set.  If false the color will
        only be changed if it has not been set by a module.
        (default False)
    format: display format for this module (default '{output}')
    gradient: The colors we will cycle through, This is a list of hex values
        *(default [ '#FF0000', '#FFFF00', '#00FF00', '#00FFFF',
        '#0000FF', '#FF00FF', '#FF0000', ])*
    multi_color: If True then each module the rainbow contains will be colored
        differently (default True)
    steps: Number of steps between each color in the gradient
        (default 10)

Format placeholders:
    {output} rainbow output

Examples:
```
# show time colorfully
order += "rainbow time"
rainbow time {
    time {}
}

# blinking text black/white
order += "rainbow blink_time"
rainbow blink_time {
    gradient = [
        '#FFFFFF',
        '#000000',
    ]
    steps = 1
    time {}
}
```

@author tobes

SAMPLE OUTPUT
[
    {'color': '#FF0000', 'full_text': 'module 1'},
    {'color': '#CCFF00', 'full_text': 'module 2', 'separator': True},
    {'color': '#00FF66', 'full_text': 'module 3', 'separator': True},
    {'color': '#0066FF', 'full_text': 'module 4', 'separator': True},
    {'color': '#CC00FF', 'full_text': 'module 5', 'separator': True}
]
"""

from __future__ import division
import re
import math
from time import time

HEX_RE = re.compile("#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})")


class Py3status:
    """
    """

    # available configuration parameters
    cycle_time = 1
    force = False
    format = "{output}"
    gradient = [
        "#FF0000",
        "#FFFF00",
        "#00FF00",
        "#00FFFF",
        "#0000FF",
        "#FF00FF",
        "#FF0000",
    ]
    multi_color = True
    steps = 10

    class Meta:
        container = True

    def post_config_hook(self):
        def from_hex(color):
            """
            Convert hex color #xxx or #xxxxxx to [r, g, b].
            """
            if not HEX_RE.match(color):
                color = "#FFF"
            if len(color) == 7:
                return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:], 16))
            return (
                int(color[1], 16) * 17,
                int(color[2], 16) * 17,
                int(color[3], 16) * 17,
            )

        def to_hex(color):
            """
            Convert [r, g, b] to hex.
            """
            return "#{:02X}{:02X}{:02X}".format(
                int(color[0]), int(color[1]), int(color[2])
            )

        def make_color(c1, c2, t):
            """
            Generate a mid color between c1 and c2.
            """

            def fade(i):
                a = c1[i]
                b = c2[i]
                x = b * t
                x += a * (1 - t)
                return x

            c1 = from_hex(c1)
            c2 = from_hex(c2)
            return (fade(0), fade(1), fade(2))

        colors = []
        if self.steps == 1:
            colors = [to_hex(from_hex(x)) for x in self.gradient]
        else:
            for i in range(len(self.gradient) - 1):
                for j in range(self.steps):
                    colors.append(
                        to_hex(
                            make_color(
                                self.gradient[i], self.gradient[i + 1], j / (self.steps)
                            )
                        )
                    )
        self.colors = colors
        self.active_color = 0
        self._set_cycle_time()

    def _set_cycle_time(self):
        """
        Set next cycle update time synced to nearest second or 0.1 of second.
        """
        now = time()
        try:
            cycle_time = now - self._cycle_time
            if cycle_time < 0:
                cycle_time = 0
        except AttributeError:
            cycle_time = 0
        cycle_time += self.cycle_time
        if cycle_time == int(cycle_time):
            self._cycle_time = math.ceil(now + cycle_time)
        else:
            self._cycle_time = math.ceil((now + cycle_time) * 10) / 10
        self._cycle_time = now + self.cycle_time

    def _get_current_output(self):
        """
        Get child modules output.
        """
        output = []
        for item in self.items:
            out = self.py3.get_output(item)
            if out and "separator" not in out[-1]:
                out[-1]["separator"] = True
            output += out
        return output

    def rainbow(self):
        """
        Make a rainbow!
        """
        if not self.items:
            return {"full_text": "", "cached_until": self.py3.CACHE_FOREVER}

        if time() >= self._cycle_time - (self.cycle_time / 10):
            self.active_color = (self.active_color + 1) % len(self.colors)
            self._set_cycle_time()

        color = self.colors[self.active_color]
        content = self._get_current_output()
        output = []

        if content:
            step = len(self.colors) // len(content)
        for index, item in enumerate(content):
            if self.multi_color:
                offset = (self.active_color + (index * step)) % len(self.colors)
                color = self.colors[offset]
            obj = item.copy()
            if self.force or not obj.get("color"):
                obj["color"] = color
            output.append(obj)

        composites = {"output": self.py3.composite_create(output)}
        rainbow = self.py3.safe_format(self.format, composites)

        return {"cached_until": self._cycle_time, "full_text": rainbow}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
