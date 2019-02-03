# -*- coding: utf-8 -*-
"""
Display keyboard layout.

Configuration parameters:
    button_next: mouse button to cycle next layout (default 4)
    button_prev: mouse button to cycle previous layout (default 5)
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{layout}')
    layouts: specify a list of layouts to use (default None)

Format placeholders:
    {layout} keyboard layout

Color options:
    color_<layout>: colorize the layout. eg color_fr = '#729FCF'

Requires:
    xkblayout-state:
        or
    setxkbmap: and `xset` (works for the first two predefined layouts.)

Examples:
```
# define keyboard layouts that can be switched between
keyboard_layout {
    layouts = ['gb', 'fr', 'dvorak']
}
```

@author shadowprince, tuxitop
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': 'gb'}

fr
{'color': '#268BD2', 'full_text': 'fr'}

ru
{'color': '#F75252', 'full_text': 'ru'}

ua
{'color': '#FCE94F', 'full_text': 'ua'}

us
{'color': '#729FCF', 'full_text': 'us'}

"""

import re

LAYOUTS_RE = re.compile(r".*layout:\s*((\w+,?)+).*", flags=re.DOTALL)
LEDMASK_RE = re.compile(r".*LED\smask:\s*\d{4}([01])\d{3}.*", flags=re.DOTALL)
VARIANTS_RE = re.compile(r".*variant:\s*(([\w-]+,?)+).*", flags=re.DOTALL)


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_prev = 5
    cache_timeout = 10
    format = "{layout}"
    layouts = None

    def post_config_hook(self):
        self.colors = getattr(self, "colors", None)  # old config
        try:
            self._xkblayout()
            self._command = self._xkblayout
        except self.py3.CommandError:
            self._command = self._setxkbmap

        if not self.layouts:
            self.layouts = []
        # We use a copy of layouts so that we can add extra layouts without
        # affecting the original list
        self._layouts = self.layouts[:]
        self._last_layout = None

        self.colors_dict = {}
        # old compatibility: set default values
        self.defaults = {
            "fr": "#268BD2",
            "ru": "#F75252",
            "ua": "#FCE94F",
            "us": "#729FCF",
        }

    def keyboard_layout(self):
        layout, variant = self._command()
        # If the current layout is not in our layouts list we need to add it
        if layout not in self._layouts:
            self._layouts = [layout] + self.layouts
            self._active = 0
        # show new layout if it has been changed externally
        if layout != self._last_layout:
            self._active = self._layouts.index(layout)
            self._last_layout = layout
        lang = self._layouts[self._active]

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format, {"layout": lang, "variant": variant}
            ),
        }

        if self.colors and not self.colors_dict:
            self.colors_dict = dict(
                (k.strip(), v.strip())
                for k, v in (layout.split("=") for layout in self.colors.split(","))
            )

        # colorize languages containing spaces and/or dashes too
        language = lang.upper()
        for character in " -":
            if character in language:
                language = language.replace(character, "_")

        lang_color = getattr(self.py3, "COLOR_%s" % language)
        if not lang_color:
            lang_color = self.colors_dict.get(lang)
        if not lang_color:  # old compatibility: try default value
            lang_color = self.defaults.get(lang)
        if lang_color:
            response["color"] = lang_color

        return response

    def _xkblayout(self):
        layout, variant = [
            x.strip()
            for x in self.py3.command_output(
                ["xkblayout-state", "print", "%s|SEPARATOR|%v"]
            ).split("|SEPARATOR|")
        ]
        return layout, variant

    def _setxkbmap(self):
        # this method works only for the first two predefined layouts.
        out = self.py3.command_output(["setxkbmap", "-query"])
        layouts = re.match(LAYOUTS_RE, out).group(1).split(",")
        if len(layouts) == 1:
            variant = re.match(VARIANTS_RE, out)
            if variant:
                variant = variant.group(1)
                return "{} {}".format(layouts[0], variant), variant
            else:
                return layouts[0], ""

        xset_output = self.py3.command_output(["xset", "-q"])
        led_mask = re.match(LEDMASK_RE, xset_output).groups(0)[0]
        return layouts[int(led_mask)], ""

    def _set_active(self, delta):
        self._active += delta
        self._active = self._active % len(self._layouts)
        layout = self._layouts[self._active]
        self.py3.command_run("setxkbmap -layout {}".format(layout))

    def on_click(self, event):
        button = event["button"]
        if button == self.button_next:
            self._set_active(1)
        if button == self.button_prev:
            self._set_active(-1)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
