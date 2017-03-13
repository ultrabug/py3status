# -*- coding: utf-8 -*-
from __future__ import division

import ast
import os
import re
from hashlib import md5

try:
    import cairo
    import pango
    import pangocairo
except ImportError:
    cairo = None

WIDTH = 650
TOP_BAR_HEIGHT = 5
BAR_HEIGHT = 25
HEIGHT = TOP_BAR_HEIGHT + BAR_HEIGHT
X_OFFSET = 5.5
SEP_PADDING = 5
SEP_BORDER = 3

# FONT = 'Ubuntu Mono 13'
# FONT = 'Inconsolata 13'
FONT = 'DejaVu Sans Mono 11'

COLOR = '#FFFFFF'
COLOR_BG = '#000000'

COLOR_PY3STATUS = '#FFFFFF'
COLOR_MODULE_NAME = None

HEX_DIDGETS = '0123456789abcdefABCDEF'
HEX_2_DEC = {v: int(v, 16)
             for v in (x + y for x in HEX_DIDGETS for y in HEX_DIDGETS)}


def get_color_for_name(module_name):
    """
    Create a custom color for a given string.
    This allows the screenshots to each have a unique color but for that color
    to be consistent.
    """
    saturation = 0.5
    value = 243.2
    hue = int(md5(module_name).hexdigest(), 16) / 16**32
    hue *= 6
    hue += 3.708
    return '#' + '%02x' * 3 % (
        (value, value - value * saturation * abs(1 - hue % 2), value - value *
         saturation) * 3)[5**int(hue) // 3 % 3::int(hue) % 2 + 1][:3]


def hex_2_rgb(hex):
    """
    convert a hex color to rgb
    """
    hex = hex[1:]
    return HEX_2_DEC[hex[0:2]] / 255, HEX_2_DEC[hex[2:4]] / 255, HEX_2_DEC[hex[
        4:6]] / 255


class ImageMaker:
    """
    Class for creating screenshot images

    Screenshots are created from sample output data in module docstring
    """

    def __init__(self, img_path):
        self.img_path = img_path

    def create_screenshot(self, name, data, quiet):
        """
        create a screenshor from module data
        """
        self.x = X_OFFSET
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
        cr = cairo.Context(surface)

        cr.set_line_width(1)
        desktop_color = get_color_for_name(name)
        cr.set_source_rgb(*hex_2_rgb(desktop_color))

        cr.rectangle(0, 0, WIDTH, TOP_BAR_HEIGHT)
        cr.fill()
        cr.set_source_rgb(*hex_2_rgb(COLOR_BG))
        cr.rectangle(0, TOP_BAR_HEIGHT, WIDTH, BAR_HEIGHT)
        cr.fill()

        pangocairo_context = pangocairo.CairoContext(cr)
        pangocairo_context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        font = pango.FontDescription(FONT)

        def text(text, separator=True, color=None):
            """
            Add text to the image, including separator if needed.
            """

            if separator and self.x != X_OFFSET:
                cr.set_source_rgb(*hex_2_rgb(COLOR))
                self.x += SEP_PADDING
                cr.move_to(WIDTH - self.x, TOP_BAR_HEIGHT + SEP_BORDER)
                cr.line_to(WIDTH - self.x, BAR_HEIGHT + TOP_BAR_HEIGHT - SEP_BORDER)
                cr.stroke()
                self.x += SEP_PADDING

            layout = pangocairo_context.create_layout()

            layout.set_font_description(font)
            layout.set_text(text)
            width, height = layout.get_pixel_size()

            self.x += width
            y = ((BAR_HEIGHT - height) / 2) + TOP_BAR_HEIGHT
            cr.set_source_rgb(*hex_2_rgb(color or COLOR))
            cr.save()
            cr.translate(WIDTH - self.x, y)
            pangocairo_context.update_layout(layout)
            pangocairo_context.show_layout(layout)
            cr.restore()

        text('py3status', color=COLOR_PY3STATUS)
        text(name.split('-')[0], color=COLOR_MODULE_NAME or desktop_color)
        separator = True
        if not isinstance(data, list):
            data = [data]

        for item in reversed(data):
            text(text=item.get('full_text'),
                 color=item.get('color'),
                 separator=item.get('separator', separator))
            separator = False

        file_name = '%s.png' % name
        surface.write_to_png(os.path.join(self.img_path, file_name))
        if not quiet:
            print(file_name)


def parse_sample_data(sample_data, module_name):
    """
    Parse sample output definitions and return a dict
    {screenshot_name: sample_output}
    """
    samples = {}
    name = None
    data = ''
    count = 0
    for line in sample_data.splitlines() + ['']:
        if line == '':
            if data:
                if name:
                    name = u'%s-%s-%s' % (module_name, count, name)
                else:
                    name = module_name
                try:
                    samples[name] = ast.literal_eval(data)
                except:
                    samples[name] = 'SAMPLE DATA ERROR'
                name = None
                data = ''
                count += 1
            continue
        if name is None and data == '' and not line[0] in ['[', '{']:
            name = line
            continue
        else:
            data += line
    return samples


def get_samples():
    '''
    Look in all core modules and get any samples from the docstrings.
    return a dict {screenshot_name: sample_output}
    '''
    samples = {}
    module_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'modules')
    for file in sorted(os.listdir(module_dir)):
        if file.endswith('.py') and file != '__init__.py':
            module_name = file[:-3]
            with open(os.path.join(module_dir, file)) as f:
                module = ast.parse(f.read())
                raw_docstring = ast.get_docstring(module)
                if raw_docstring is None:
                    continue
                parts = re.split('^SAMPLE OUTPUT$', raw_docstring, flags=re.M)
                if len(parts) == 1:
                    continue
                sample_data = parts[1]
                samples.update(parse_sample_data(sample_data, module_name))
    return samples


def create_screenshots(quiet=False):
    """
    create screenshots for all core modules.
    The screenshots directory will have all .png files deleted before new shots
    are created.
    """
    if cairo is None:
        print('cairo, pango, or pangocairo modules not installed.')
        return

    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'screenshots'
    )
    # create dir if not exists
    try:
        os.makedirs(path)
    except OSError:
        pass
    # delete all existing screenshots
    test = os.listdir(path)

    for item in test:
        if item.endswith(".png"):
            os.remove(os.path.join(path, item))

    print('Creating screenshots...')
    image_maker = ImageMaker(path)
    for k, v in get_samples().items():
        image_maker.create_screenshot(k, v, quiet=quiet)
