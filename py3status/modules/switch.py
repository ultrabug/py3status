# -*- coding: utf-8 -*-
"""
Switch next or previous commands in the list.

Configuration parameters:
    button_action: mouse button to take action (default None)
    button_next: mouse button to switch next item (default None)
    button_previous: mouse button to switch previous item (default None)
    button_reset: mouse button to reset an index (default None)
    format: display format for this module (default '{list}')
    initial: specify an index to initialize (default 1)
    list: specify a list of tuples, eg [('name', 'command')],
        to format and run if switched to visibility (default [])
    loop: iterate through the list in a loop manner (default False)
    reset: specify an index to reset, otherwise initial (default None)

Format placeholders:
    {list} a list of names to be formatted and commands to be executed

Control list placeholders:
    index: list index (first items only)

Note:
    Short explanation. The list is simply a list of 2-tuples.
    The first items will be formatted. The second items will be executed. eg,
        list = [
            ('first_name', 'first_command'),
            ('second_name', 'second_command'),
        ]

Examples:
```
# emulate dpms switching
switch dpms {
    button_action = 1
    list = [
        ('\?color=good DPMS', 'xset +dpms s on'),
        ('\?color=bad DPMS', 'xset -dpms s off'),
    ]
}

# create keyboard_layout switching
switch keyboard_layout {
    button_next = 4
    button_previous = 5
    list = [
        ('\?color=#268BD2 fr', 'setxkbmap fr'),
        ('\?color=#F75252 ru', 'setxkbmap ru'),
        ('\?color=#FCE94F ua', 'setxkbmap ua'),
        ('\?color=#729FCF us', 'setxkbmap us'),
    ]
}

# emulate xrandr switching - use arandr to create scripts
switch xrandr {
    button_action = 1
    button_next = 4
    button_previous = 5
    loop = True
    list = [
        ('\?if=index=1&color=good normal,normal|normal,normal',
            '~/.screenlayout/arandr-normal-normal.sh'),
        ('\?if=index=2&color=good left,normal|left,normal',
            '~/.screenlayout/arandr-left-normal.sh'),
        ('\?if=index=3&color=good left,left|left,left',
            '~/.screenlayout/arandr-left-left.sh'),
        ('\?if=index=4&color=good normal,left|normal,left',
            '~/.screenlayout/arandr-normal-left.sh'),
    ]
}

# emulate xrandr_rotate switching - use arandr to create scripts
switch xrandr_rotate {
    button_action = 1
    button_next = 4
    button_previous = 5
    loop = True
    list = [
        ('\?if=index=1&color=good normal|normal',
            '~/.screenlayout/arandr-normal-normal.sh'),
        ('\?if=index=2&color=good left|left',
            '~/.screenlayout/arandr-left-left.sh'),
        ('\?if=index=3&color=good inverted|inverted',
            '~/.screenlayout/arandr-inverted-inverted.sh'),
        ('\?if=index=4&color=good right|right',
            '~/.screenlayout/arandr-right-right.sh'),
    ]
}

# emulate hueshift switching
switch hueshift {
    button_next = 4
    button_previous = 5
    button_reset = 3
    initial = 7
    list = [
        ('\?color=#f3c \u263c 1000K', 'redshift -r -O 1000'),
        ('\?color=#f3c \u263c 2000K', 'redshift -r -O 2000'),
        # good stop - my opinion
        ('\?color=#f3c \u263c 3000K', 'redshift -r -O 3000'),
        ('\?color=#f3c \u263c 4000K', 'redshift -r -O 4000'),
        ('\?color=#f3c \u263c 5000K', 'redshift -r -O 5000'),
        ('\?color=#f3c \u263c 6000K', 'redshift -r -O 6000'),
        ('\?color=#ff3 \u263c 6500K', 'redshift -r -O 6500'),
        ('\?color=#3cf \u263c 7000K', 'redshift -r -O 7000'),
        ('\?color=#3cf \u263c 8000K', 'redshift -r -O 8000'),
        ('\?color=#3cf \u263c 9000K', 'redshift -r -O 9000'),
        ('\?color=#3cf \u263c 10000K', 'redshift -r -O 10000'),
        # good stop - my opinion - up to 10000K for sct
        ('\?color=#3cf \u263c 11000K', 'redshift -r -O 11000'),
        ('\?color=#3cf \u263c 12000K', 'redshift -r -O 12000'),
        ('\?color=#3cf \u263c 13000K', 'redshift -r -O 13000'),
        ('\?color=#3cf \u263c 14000K', 'redshift -r -O 14000'),
        ('\?color=#3cf \u263c 15000K', 'redshift -r -O 15000'),
        # et cetera... up to 25000K for redshift and blueshift
        ('\?color=#3cf \u263c 16000K', 'redshift -r -O 16000'),
        ('\?color=#3cf \u263c 17000K', 'redshift -r -O 17000'),
        ('\?color=#3cf \u263c 18000K', 'redshift -r -O 18000'),
        ('\?color=#3cf \u263c 19000K', 'redshift -r -O 19000'),
        ('\?color=#3cf \u263c 20000K', 'redshift -r -O 20000'),
        ('\?color=#3cf \u263c 21000K', 'redshift -r -O 21000'),
        ('\?color=#3cf \u263c 22000K', 'redshift -r -O 22000'),
        ('\?color=#3cf \u263c 23000K', 'redshift -r -O 23000'),
        ('\?color=#3cf \u263c 24000K', 'redshift -r -O 24000'),
        ('\?color=#3cf \u263c 25000K', 'redshift -r -O 25000'),
    ]
}

# emulate volume_status switching
switch volume_status {
    button_next = 4
    button_previous = 5
    button_reset = 3
    initial = 1
    color_boost = '#11ff99'
    # note: my default sink number is 0
    list = [
        ('\?color=degraded \[M\]', 'pactl -- set-sink-mute 0 1'),
        ('\?color=degraded {M}', 'pactl -- set-sink-mute 0 0'),
        ('\?color=bad  0%', 'pactl -- set-sink-volume 0 0%'),
        ('\?color=bad  1%', 'pactl -- set-sink-volume 0 1%'),
        ('\?color=bad  2%', 'pactl -- set-sink-volume 0 2%'),
        ('\?color=bad  3%', 'pactl -- set-sink-volume 0 3%'),
        ('\?color=bad  4%', 'pactl -- set-sink-volume 0 4%'),
        ('\?color=bad  5%', 'pactl -- set-sink-volume 0 5%'),
        ('\?color=bad  10%', 'pactl -- set-sink-volume 0 10%'),
        ('\?color=bad  15%', 'pactl -- set-sink-volume 0 15%'),
        ('\?color=degraded  20%', 'pactl -- set-sink-volume 0 20%'),
        ('\?color=degraded  25%', 'pactl -- set-sink-volume 0 25%'),
        ('\?color=degraded  30%', 'pactl -- set-sink-volume 0 30%'),
        ('\?color=degraded  35%', 'pactl -- set-sink-volume 0 35%'),
        ('\?color=degraded  40%', 'pactl -- set-sink-volume 0 40%'),
        ('\?color=degraded  45%', 'pactl -- set-sink-volume 0 45%'),
        ('\?color=good  50%', 'pactl -- set-sink-volume 0 50%'),
        ('\?color=good  55%', 'pactl -- set-sink-volume 0 55%'),
        ('\?color=good  60%', 'pactl -- set-sink-volume 0 60%'),
        ('\?color=good  65%', 'pactl -- set-sink-volume 0 65%'),
        ('\?color=good  70%', 'pactl -- set-sink-volume 0 70%'),
        ('\?color=good  75%', 'pactl -- set-sink-volume 0 75%'),
        ('\?color=good  80%', 'pactl -- set-sink-volume 0 80%'),
        ('\?color=good  85%', 'pactl -- set-sink-volume 0 85%'),
        ('\?color=good  90%', 'pactl -- set-sink-volume 0 90%'),
        ('\?color=good  95%', 'pactl -- set-sink-volume 0 95%'),
        ('\?color=good  100%', 'pactl -- set-sink-volume 0 100%'),
        ('\?color=boost ! 105%', 'pactl -- set-sink-volume 0 105%'),
        ('\?color=boost ! 110%', 'pactl -- set-sink-volume 0 110%'),
        ('\?color=boost ! 115%', 'pactl -- set-sink-volume 0 115%'),
        ('\?color=boost ! 120%', 'pactl -- set-sink-volume 0 120%'),
    ]
}

# create directory_menu switching
switch directory_menu {
    button_action = 1
    button_next = 4
    button_previous = 5
    color_dir = '#00ffff'
    list = [
        ('\?color=dir Home', 'nautilus /home/lasers'),
        ('\?color=dir Desktop', 'nautilus /home/lasers/Desktop'),
        ('\?color=dir Documents', 'nautilus /home/lasers/Documents'),
        ('\?color=dir Downloads', 'nautilus /home/lasers/Downloads'),
        ('\?color=dir Music', 'nautilus /home/lasers/Music'),
        ('\?color=dir Pictures', 'nautilus /home/lasers/Pictures'),
        ('\?color=dir Videos', 'nautilus /home/lasers/Videos'),
        ('\?color=dir Trash', 'nautilus trash:///'),
    ]
}

# create favorite_sites switching
switch favorite_sites {
    button_action = 1
    button_next = 4
    button_previous = 5
    color_site = '#ffccff'
    list = [
        ('\?color=site py3status', 'xdg-open https://github.com/ultrabug/py3status'),
        ('\?color=site Amazon', 'xdg-open https://www.amazon.com'),
        ('\?color=site Facebook', 'xdg-open https://www.facebook.com'),
        ('\?color=site Github', 'xdg-open https://www.github.com'),
        ('\?color=site Gmail', 'xdg-open https://mail.google.com'),
        ('\?color=site Google', 'xdg-open https://www.google.com'),
        ('\?color=site Netflix', 'xdg-open https://www.netflix.com'),
        ('\?color=site Twitter', 'xdg-open https://www.twitter.com'),
        ('\?color=site Wikipedia', 'xdg-open https://www.wikipedia.org'),
        ('\?color=site YouTube', 'xdg-open https://www.youtube.com'),
    ]
}

# create favorite_apps switching
switch favorite_apps {
    button_action = 1
    button_next = 4
    button_previous = 5
    color_app = '#ccff00'
    list = [
        ('\?color=app py3status', 'notify-send py3status rocks!'),
        ('\?color=app calibre', 'calibre'),
        ('\?color=app firefox', 'firefox'),
        ('\?color=app gimp', 'gimp'),
        ('\?color=app gvim', 'gvim'),
        ('\?color=app i3lock', 'i3lock'),
        ('\?color=app lxappearance', 'lxappearance'),
        ('\?color=app nautilus', 'nautilus'),
        ('\?color=app passmenu', 'passmenu'),
        ('\?color=app random-wallpaper', '~/path/to/random_wallpaper.sh'),
        ('\?color=app urxvt', 'urxvt'),
    ]
}

# add your snippets here
switch {
    format = '...'
}
```

@author lasers

SAMPLE OUTPUT
index-1
{'color': '#00FF00', 'full_text': 'first index'}

index-2
{'color': '#00FF00', 'full_text': 'second index'}

index-3
{'color': '#0000FF', 'full_text': 'third index'}
"""

import shlex
from os import setpgrp
from os.path import expanduser
from subprocess import Popen
STRING_ERROR = 'missing list'


class Py3status:
    """
    """
    # available configuration parameters
    button_action = None
    button_next = None
    button_previous = None
    button_reset = None
    format = '{list}'
    initial = 1
    list = []
    loop = False
    reset = None

    def post_config_hook(self):
        if not self.list:
            raise Exception(STRING_ERROR)
        self.length = len(self.list)
        if self.initial == -1:
            self.initial = self.length
        if not 1 <= self.initial <= self.length:
            self.initial = 1
        self.active_index = self.initial
        if not self.reset:
            self.reset = self.initial
        self.can_reset = 1 <= self.reset <= self.length
        self.can_next = not any([self.button_next, self.button_previous])
        if self.can_next:
            self.loop = True
        self.index = None
        self.is_action = True
        self.new_list = {}
        for index, (name, cmd) in enumerate(self.list, 1):
            self.new_list[index] = {'name': name, 'command': expanduser(cmd)}
        self.button_list = [self.button_action, self.button_next,
                            self.button_previous, self.button_reset]

    def switch(self):
        if not self.button_action or self.is_action:
            Popen(shlex.split(
                self.new_list[self.active_index]['command']), preexec_fn=setpgrp)
            self.index = self.active_index
            self.is_action = False

        format_list = self.py3.safe_format(
            self.new_list[self.active_index]['name'], {'index': self.index})

        return {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(
                self.format, {'list': format_list}),
        }

    def on_click(self, event):
        button = event['button']
        if button == self.button_action:
            self.is_action = True
        elif button == self.button_previous:
            self.active_index -= 1
            if self.active_index < 1:
                self.active_index = self.length if self.loop else 1
        if button == self.button_next or self.can_next:
            self.active_index += 1
            if self.active_index > self.length:
                self.active_index = 1 if self.loop else self.length
        if button == self.button_reset and self.can_reset:
            self.active_index = self.reset
        if button not in self.button_list:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
