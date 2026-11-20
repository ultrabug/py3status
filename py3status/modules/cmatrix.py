r"""
Display falling characters like The Matrix.

Inspired by cmatrix. Each column is one cell of a drop falling past the bar:
a white head, then a trail that fades as it ages, then nothing until the next
drop. Drops vary in length and spacing, so every column rains at its own pace.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 0.1)
    color: specify a color to use, eg green or random (default 'lime')
    format: display format for this module (default '{matrix}')
    length: specify a number of columns to show (default 20)

Format placeholders:
    {matrix} falling characters

Examples:
```
# show a wider matrix in amber
cmatrix {
    color = "orange"
    length = 40
}

# colorize red, like cmatrix -C red
cmatrix {
    color = "red"
}

# pick a random color on startup
cmatrix {
    color = "random"
}

# colorize rainbow, like cmatrix -r
rainbow {
    cycle_time = 0.1
    force = True
    cmatrix {}
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'k ', 'color': '#00CD00'},
    {'full_text': '  '},
    {'full_text': '7 ', 'color': '#FFFFFF'},
    {'full_text': 'H', 'color': '#00FF00'},
]
"""

from random import choice, randint

from py3status.constants import COLOR_NAMES
from py3status.formatter import expand_color

LINES = 24  # cmatrix sizes streams and gaps by terminal height
STRING_INVALID_COLOR = "invalid color"


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 0.1
    color = "lime"
    format = "{matrix}"
    length = 20

    def post_config_hook(self):
        if self.color == "random":
            self.color = choice(list(COLOR_NAMES))
        color = expand_color(self.color.lower())
        if not color:
            raise Exception(STRING_INVALID_COLOR)
        # start every column empty with a random gap, so drops don't fall in step
        self.columns = [
            {"char": " ", "color": None, "length": 0, "spaces": randint(1, LINES)}
            for _ in range(self.length)
        ]
        # fade trails in steps
        self.shades = [
            "#{:02X}{:02X}{:02X}".format(
                *[int(color[i : i + 2], 16) * step // 255 for i in (1, 3, 5)]
            )
            for step in (255, 205, 155, 105)
        ]

    def _get_matrix(self):
        matrix = []
        for column in self.columns:
            if column["length"]:
                column["length"] -= 1
                age = column["total"] - column["length"]
                column["color"] = self.shades[(age - 1) * len(self.shades) // column["total"]]
            elif column["color"]:
                column.update(char=" ", color=None, spaces=randint(1, LINES))
            elif column["spaces"]:
                column["spaces"] -= 1
            else:
                length = randint(3, LINES - 1)
                column.update(
                    char=chr(randint(33, 122)), color="#FFFFFF", length=length, total=length
                )
            # rain falls in every other column like cmatrix
            matrix.append({"full_text": column["char"] + " "})
            if column["color"]:
                matrix[-1]["color"] = column["color"]

        matrix[-1]["full_text"] = matrix[-1]["full_text"][:-1]
        return matrix

    def cmatrix(self):
        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format, {"matrix": self.py3.composite_create(self._get_matrix())}
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
