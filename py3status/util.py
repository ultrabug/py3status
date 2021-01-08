import re
from colorsys import rgb_to_hsv, hsv_to_rgb
from math import modf


class Gradients:
    """
    Create color gradients
    """

    RE_HEX = re.compile("#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})")

    _gradients_cache = {}

    def hex_2_rgb(self, color):
        """
        convert a hex color to rgb
        """
        if not self.RE_HEX.match(color):
            color = "#FFF"
        if len(color) == 7:
            return (int(color[i : i + 2], 16) / 255 for i in [1, 3, 5])
        return (int(c, 16) / 15 for c in color)

    def rgb_2_hex(self, r, g, b):
        """
        convert a rgb color to hex
        """
        return "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))

    def hex_2_hsv(self, color):
        """
        convert a hex color to hsv
        """
        return rgb_to_hsv(*self.hex_2_rgb(color))

    def hsv_2_hex(self, h, s, v):
        """
        convert a hsv color to hex
        """
        return self.rgb_2_hex(*hsv_to_rgb(h, s, v))

    def make_mid_color(self, color1, color2, distance, long_route=False):
        """
        Generate a mid color between color1 and color2.
        Colors should be a tuple (hue, saturation, value).

        distance is a float between 0.0 and 1.0 describing how far between
        color1 and color2 we want to return the color. 0.0 would return color1,
        1.0 color2, and 0.5 a color midway.

        long_route allows us to choose how we get from color1 to color2 around
        the color wheel if True we go the long way, through as many colors as
        we can, if False we go through the minimum number
        """

        def fade(a, b):
            x = b * distance
            x += a * (1 - distance)
            return x

        h1, s1, v1 = color1
        h2, s2, v2 = color2

        hue_diff = h1 - h2
        if long_route:
            if -0.5 < hue_diff < 0.5:
                h1 += 1
        else:
            if hue_diff > 0.5:
                h2 += 1
            elif hue_diff < -0.5:
                h1 += 1
        return (modf(fade(h1, h2))[0], fade(s1, s2), fade(v1, v2))

    def generate_gradient(self, color_list, size=101):
        """
        Create a gradient of size colors that passes through the colors
        give in the list (the resultant list may not be exactly size long).
        The gradient will be evenly distributed.
        colors should be in hex format eg '#FF00FF'
        """
        list_length = len(color_list)
        gradient_step = size / (list_length - 1)

        gradient_data = []
        for x in range(list_length):
            gradient_data.append((int(gradient_step * x), color_list[x]))

        data = []
        for (start, color1), (end, color2) in zip(gradient_data, gradient_data[1:]):
            color1 = self.hex_2_hsv(color1)
            color2 = self.hex_2_hsv(color2)

            steps = end - start
            for j in range(steps):
                data.append(
                    self.hsv_2_hex(*self.make_mid_color(color1, color2, j / steps))
                )
        data.append(self.hsv_2_hex(*color2))
        return data

    def make_threshold_gradient(self, py3, thresholds, size=100):

        """
        Given a thresholds list, creates a gradient list that covers the range
        of the thresholds.
        The number of colors in the gradient is limited by size.
        Because of how the range is split the exact number of colors in the
        gradient cannot be guaranteed.
        """
        thresholds = sorted(thresholds)
        key = f"{thresholds}|{size}"
        try:
            return self._gradients_cache[key]
        except KeyError:
            pass
        minimum = min(thresholds)[0]
        maximum = max(thresholds)[0]
        if maximum - minimum > size:
            steps_size = size / (maximum - minimum)
        else:
            steps_size = 1
        colors = []
        for thres_a, thres_b in zip(thresholds, thresholds[1:]):
            color_list = [thres_a[1], thres_b[1]]
            num_colors = int((thres_b[0] - thres_a[0]) * steps_size)
            colors.extend(self.generate_gradient(color_list, num_colors))
        # cache gradient
        self._gradients_cache[key] = colors
        return colors
