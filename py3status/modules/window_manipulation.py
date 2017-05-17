# -*- coding: utf-8 -*-
"""
Display windows and scratchpads asynchronously.

Lo and behold! A swiss army knife of window management and/or manipulation
that can be done asynchronously! This module aims to support a wide range of
window customization needs (if applicable). This covers the features already
available on other modules and can perform some fairly well magic.

This module welcomes more cowbell to make new manipulations possible.

Configuration parameters:
    button_focus: mouse button to focus a window (default None)
    button_next: mouse button to focus next window (default None)
    button_previous: mouse button to focus previous window (default None)
    events: list of events for this module to subscribe.
        For more information, visit https://i3wm.org/docs/ipc.html#_events
        (default [])
    format: display format for this module (default None)
    format_scratchpad: display format for scratchpad windows (default None)
    format_separator: show separator only if more than one (default ' ')
    format_window: display format for windows (default None)
    thresholds: color thresholds to use (default [])
    use_urgent: urgent to enable, otherwise disabled.
        'window': all windows including the scratchpad windows.
        'scratchpad': scratchpad windows only.
        (default None)

Format placeholders:
    {format_scratchpad}  format for scratchpad windows   eg (new output here)
    {format_window}      format for windows              eg (new output here)
    {id}                 window id                       eg 12345678
    {name}               window name                     eg lasers@z420
    {class}              window class                    eg URxvt
    {percent}            window percent                  eg 1.0
    {pixel}              number of border pixels         eg 2
    {floating}           number of floating windows      eg 3
    {scratchpad}         number of scratchpad windows    eg 4
    {urgent_window}      number of urgents               eg 2
    {urgent_scratchpad}  number of scratchpad urgents    eg 1
    {window}             number of windows               eg 11
    is_none              a boolean based on window data
    is_normal            a boolean based on window data
    is_pixel             a boolean based on window data
    is_splith            a boolean based on window data
    is_splitv            a boolean based on window data
    is_stacked           a booelan based on window data
    is_tabbed            a boolean based on window data

format_scratchpad placeholders:
    {index}              window index                    eg 1
    {id}                 window id                       eg 12345678
    {name}               window name                     eg lasers@z420
    {pixel}              number of border pixels         eg 2
    {class}              window class                    eg URxvt
    is_focused           a boolean based on window data
    is_urgent            a boolean based on window data

format_window placeholders:
    {index}              window index                    eg 5
    {id}                 window id                       eg 12345678
    {name}               window name                     eg lasers@z420
    {class}              window class                    eg URxvt
    {percent}            window percent                  eg 0.5
    {pixel}              number of border pixels         eg 2
    is_floating          a boolean based on window data
    is_focused           a boolean based on window data
    is_none              a boolean based on window data
    is_normal            a boolean based on window data
    is_pixel             a boolean based on window data
    is_scratchpad        a boolean based on window data
    is_splith            a boolean based on window data
    is_splitv            a boolean based on window data
    is_stacked           a booelan based on window data
    is_tabbed            a boolean based on window data
    is_urgent            a boolean based on window data

Color thresholds:
    index                color threshold of window index
    indexage             color threshold of window index (focused)
    percent              color threshold of window percent
    percentage           color threshold of window percent (focused)
    pixel                color threshold of window border pixel
    pixelage             color threshold of window border pixel (focused)

Requires:
    i3ipc-python: an improved python library to control i3wm

@author lasers

Examples:
```
# subscribe to events
window_manipulation {
    # this module comes with no default settings. this option allows the users
    # to decide what kind of events they would like to subscribe to. here's an
    # example of registering two events to get the ball rolling.
    events = ['window::focus', 'window::urgent']
}

# show title
window_manipulation {
    format = '\?max_length=99 {name}'
}

# show title only on windows with none or pixel border
window_manipulation {
    format = '\?max_length=99 [\?if=is_none {name}][\?if=is_pixel {name}]'
}

# don't show the title when it's still visible (e.g. tabbed or stacked layout)
window_manipulation {
    format = '\?max_length=99 '
    format += '\?if=is_stacked '
    format += '|[\?if=is_tabbed '
    format += '|[[\?if=is_none {name}][\?if=is_pixel {name}]]'
    format += '|[[if\?if=none {name}][\?if=is_pixel {name}]]]'
}

# add buttons... for scrolling and focusing
window_manipulation {
    button_focus = 1
    button_next = 5
    button_previous = 4
}

# add colors
window_manipulation {
    color_floating = '#3DCCB0'
    color_focused = '#FFAE3D'
    color_scratchpad = '#666666'
    color_unfocused = '#3DAEE9'
    color_urgent = '#FF48C4'
}

# add window or scratchpad
window_manipulation {
    format = '{format_window}'
        OR
    format = '{format_scratchpad}'
}

# enable urgent
window_manipulation {
    use_urgent = 'window'
        OR
    use_urgent = 'scratchpad'
}

# simple urgent button
window_manipulation {
    format = '\?not_zero \u237e Urgent {urgent_window}'
    events = ['window::urgent']
    use_urgent = 'window'
}

# make dummy urgent stand out... in windows
window_manipulation {
    format = '[\?if=urgent&color=urgent URGENT] {format_window}'
}

# make dummy urgent stand out... in scratchpad
window_manipulation {
    format = '[\?if=urgent&color=urgent URGENT] {format_scratchpad}'
}

# scratchpad that works with urgent
window_manipulation {
    format = '\?not_zero&color=scratchpad ⌫ {scratchpad}'
    use_urgent = 'scratchpad'
}

# scratchpad that works with urgent (always_on, clickable)
window_manipulation {
    format = '[\?color=scratchpad&show ⌫ ]{scratchpad}'
    use_urgent = 'scratchpad'
    on_click 1 = 'exec i3-msg scratchpad show'
    on_click 3 = 'exec i3-msg move scratchpad'
}

# show all scratchpad names
window_manipulation {
    format = '[\?if=scratchpad [\?color=scratchpad ⌫ ]{format_scratchpad}]'
    format_scratchpad = '\?max_length=30 '
    format_scratchpad += '[\?if=is_urgent&color=urgent \u2756'
    format_scratchpad += '|[\?if=is_focused&color=focused \u2756'
    format_scratchpad += '|\?color=scratchpad \u2756]] {name}'
}

# show all window names
window_manipulation {
    format = '{format_window}'
    format_window = '\?max_length=30 '
    format_window += '[\?if=is_urgent&color=urgent \u2756'
    format_window += '|[\?if=is_focused&color=focused \u2756'
    format_window += '|\?color=unfocused \u2756]] {name}'
}

# show all window names excluding scratchpad windows
window_manipulation {
    format = '{format_window}'
    format_window = '\?max_length=30 '
    format_window += '[\?if=is_urgent [\?color=urgent&show \u2756] {name}'
    format_window += '|[[\?if=is_focused [\?color=focused&show \u2756] {name}'
    format_window += '|[\?if=is_scratchpad '
    format_window += '|[\?if=is_floating [\?color=floating&show \u2756] {name}'
    format_window += '|[[[\?color=unfocused&show \u2756] {name}]]]]]]]'
}

# show window names excluding floating and scratchpad windows
window_manipulation {
    format = '{format_window}'
    format_window = '\?max_length=30 '
    format_window += '[\?if=is_urgent [\?color=urgent&show \u2756] {name}'
    format_window += '|[[\?if=is_focused [\?color=focused&show \u2756] {name}]'
    format_window += '|[\?if=is_scratchpad'
    format_window += '|[\?if=is_floating'
    format_window += '|[[[\?color=unfocused&show \u2756] {name}]]]]]]'
}

# show window list
window_manipulation {
    format = '{format_window}'
    format_window = '\?max_length=30 '
    format_window += '[\?if=is_urgent [\?color=urgent&show \u2756] {name}'
    format_window += '|[[\?if=is_focused [\?color=focused&show \u2756] {name}'
    format_window += '|[\?if=is_scratchpad'
    format_window += '|[\?if=is_floating'
    format_window += '|]]]]]'
}

# show almost everything but the magic of the customizations...
# don't forget to add colors and buttons
window_manipulation {
    format = '[[\?color=#f00&show WINDOW:] {format_window}][\?soft  ]'
    format += '[[\?color=#f00&show SCRATCHPAD:] {format_scratchpad}]'
    format += '[\?color=#f00&show DIVIDER] '
    format += '[\?color=#0ff&show NAME:] {name} '
    format += '[\?color=#0ff&show CLASS:] {class} '
    format += '[\?color=#0ff&show FLOATING:] {floating} '
    format += '[\?color=#0ff&show SCRATCHPAD:] {scratchpad} '
    format += '[\?color=#0ff&show URGENT:] {urgent} '
    format += '[\?color=#0ff&show URGENT_SP:] {urgent_scratchpad} '
    format += '[\?color=#0ff&show WINDOW:] {window}'
    format += '[\?color=#0ff&show ID:] {id} '

    format_window = '\?max_length=30 [\?if=is_urgent&color=urgent \u2756'
    format_window += '|[\?if=is_focused&color=focused \u2756'
    format_window += '|[\?if=is_scratchpad&color=scratchpad \u2756'
    format_window += '|[\?if=is_floating&color=floating \u2756'
    format_window += '|\?color=unfocused \u2756]]]] {name}'

    format_scratchpad = '[\?color=#ff0&show INDEX:] {index} '
    format_scratchpad += '[\?color=#ff0&show NAME:] {name} '
    format_scratchpad += '[\?color=#ff0&show CLASS:] {class} '
    format_scratchpad += '[\?color=#ff0&show ID:] {id} '
}

# keep it simple, stupid
window_manipulation {
    format = '{format_window}'
    format_window = '\?max_length=20 [\?if=is_focused&color=good \u2756'
    format_window += '|\?color=bad \u2756] {name}'
}

# rainbow title on all windows... fun!
window_manipulation {
    format = '{format_window}'
    format_window = '\?max_length=30 \?color=index {name}'
    thresholds = [
        (1, '#ffb3ba'),
        (2, '#ffdfba'),
        (3, '#ffffba'),
        (4, '#baefba'),
        (5, '#baffc9'),
        (6, '#bae1ff'),
        (7, '#bab3ff'),
    ]
}

# danger block on all windows... fun!
window_manipulation {
    format = '{format_window}'
    format_window = '\?max_length=30 \?color=percent \u25b0'
    gradients = True
    thresholds = [
        (0.075, '#ff0000'),
        (0.425, '#ff7f00'),
        (0.675, '#ffff00'),
        (1.000, '#00ff00'),
    ]
}

# add your magic snippets here
window_manipulation {
    format = '???'
}
```

SAMPLE OUTPUT
{'full_text': u'window_manipulation'}

complicated
{'full_text': u'(too complicated)'}
"""

from threading import Thread

import i3ipc


class Py3status:
    """
    """
    # available configuration parameters
    button_focus = None
    button_next = None
    button_previous = None
    events = []
    format = None
    format_scratchpad = None
    format_separator = ' '
    format_window = None
    thresholds = []
    use_urgent = None

    def post_config_hook(self):
        if not self.format:
            raise Exception('empty format')
        if not self.events:
            raise Exception('empty events')

        if self.format_window is None:
            self.format_window = ''
        if self.format_scratchpad is None:
            self.format_scratchpad = ''

        # internal
        self._scrolling = None
        # format
        self.fmt_scratchpad = None
        self.fmt_window = None
        self.id = None
        self.window_class = None
        self.window_name = None
        self.window_percent = None
        self.window_pixel = None
        # border
        self.is_none = None
        self.is_normal = None
        self.is_pixel = None
        # layout
        self.is_stacked = None
        self.is_tabbed = None
        self.is_splith = None
        self.is_splitv = None
        # count
        self.count_floating = 0
        self.count_scratchpad = 0
        self.count_urgent_window = 0
        self.count_urgent_scratchpad = 0
        self.count_window = 0

        if self.py3.format_contains(self.format, 'format_scratchpad'):
            self._scrolling = 'scratchpad'
        if self.py3.format_contains(self.format, 'format_window'):
            self._scrolling = 'window'

        t = Thread(target=self._loop)
        t.daemon = True
        t.start()

    def _loop(self):
        try:
            def update_window_manipulation(i3, e=None):
                """
                Get everything and refresh.
                """
                scratchpads = i3.get_tree().scratchpad().leaves()
                windows = i3.get_tree().leaves()
                new_scratchpad, new_window = self._organize_data(scratchpads, windows)
                self._manipulate_and_refresh(new_scratchpad, new_window)

            i3 = i3ipc.Connection()
            update_window_manipulation(i3)

            for event in self.events:
                i3.on(event, update_window_manipulation)
            i3.main()
        except:
            self.py3.report_exception('loop error')

    def _organize_data(self, scratchpads=None, windows=None):
        """
        Grab the essentials from window and scratchpad objects and
        putting them into new dicts.  We don't alter anything here.
        """
        new_scratchpad = []
        new_window = []

        for index, s in enumerate(scratchpads, 1):
            # scratchpad: cherrypicked data
            new_scratchpad.append({
                'index': index,
                'id': s.id,
                'name': s.name,
                'pixel': s.current_border_width,
                'class': s.window_class,
                'percent': s.percent,
                'is_focused': s.focused,
                'is_urgent': s.urgent,
            })

        for index, w in enumerate(windows, 1):
            # scratchpad is an ordinary workspace. we compare window ids
            # with scratchpad ids to identify them right away.
            is_scratchpad = False
            for s in new_scratchpad:
                if w.id == s['id']:
                    is_scratchpad = True
                    break

            # window: cherrypicked data
            new_window.append({
                'index': index,
                'id': w.id,
                'name': w.name,
                'class': w.window_class,
                'border': w.border,
                'pixel': w.current_border_width,
                'layout': w.parent.layout,
                'percent': w.percent,
                'is_focused': w.focused,
                'is_urgent': w.urgent,
                'is_floating': getattr(w, 'floating', False),  # python2
                'is_scratchpad': is_scratchpad,
            })

        return new_scratchpad, new_window

    def _manipulate_and_refresh(self, in_scratchpad=None, in_window=None):
        """
        Make the results usable for the users... usually done by creating new
        and/or alter existing data. We strives to let them move through without
        any or very little manipulation. We refresh here too.
        """
        self.shared_data = in_scratchpad, in_window
        # count
        count_floating = 0
        count_scratchpad = 0
        count_urgent_window = 0
        count_urgent_scratchpad = 0
        count_window = 0

        new_scratchpad = []
        for s in in_scratchpad:
            count_scratchpad += 1
            if s['is_urgent']:
                count_urgent_scratchpad += 1

            if s['is_focused']:
                if self._scrolling == 'scratchpad':
                    self.id = s.get('id')
                # thresholds for format
                self.py3.threshold_get_color(s.get('index'), 'indexage')
                self.py3.threshold_get_color(s.get('pixel'), 'pixelage')
                self.py3.threshold_get_color(s.get('percent'), 'percentage')

            # thresholds for scratchpad
            self.py3.threshold_get_color(s.get('index'), 'index')
            self.py3.threshold_get_color(s.get('percent'), 'percent')
            new_scratchpad.append(self.py3.safe_format(self.format_scratchpad, s))

        new_window = []
        for w in in_window:
            count_window += 1
            if w['is_urgent']:
                count_urgent_window += 1

            # floating - when this gets updated, we use try and when this gets
            # scrolled, we use except because we converted the value to boolean.
            try:
                if 'on' in w['is_floating']:  # counts exclusively on updating
                    w['is_floating'] = True
                    count_floating += 1
                else:
                    w['is_floating'] = False
            except:
                if w['is_floating']:  # counts exclusively on scrolling
                    count_floating += 1

            # border - false
            w['is_normal'] = False
            w['is_pixel'] = False
            w['is_none'] = False
            # border - true
            if w['border'] == 'normal':
                w['is_normal'] = True
            elif w['border'] == 'pixel':
                w['is_pixel'] = True
            elif w['border'] == 'none':
                w['is_none'] = True

            # layout - false
            w['is_splith'] = False
            w['is_splitv'] = False
            w['is_stacked'] = False
            w['is_tabbed'] = False
            # layout - true
            if w['layout'] == 'splith':
                w['is_splith'] = True
            elif w['layout'] == 'splitv':
                w['is_splitv'] = True
            elif w['layout'] == 'stacked':
                w['is_stacked'] = True
            elif w['layout'] == 'tabbed':
                w['is_tabbed'] = True

            # send (focused) values out to the format (as placeholders) so
            # the users can do some simple things like printing name only.
            if w['is_focused']:
                if self._scrolling == 'window':
                    self.id = w.get('id')
                # format
                self.window_class = w.get('class')
                self.window_name = w.get('name')
                self.window_pixel = w.get('pixel')
                # border
                self.is_normal = w.get('is_normal')
                self.is_pixel = w.get('is_pixel')
                self.is_none = w.get('is_none')
                # layout
                self.is_splith = w.get('is_splith')
                self.is_splitv = w.get('is_splitv')
                self.is_stacked = w.get('is_stacked')
                self.is_tabbed = w.get('is_tabbed')

                # self.window_percent = ????

                # @tobes: i have this problem... wanting to use both same name
                # for format and format_window. is it possible to do that?
                # so the format can use current window's percent + color value
                # instead of using 'percentage'... otherwise, it'll just use the
                # last window's 'percent' if i used 'percent' here.

                # same thing for indexage and pixelage.

                # thresholds for format
                self.py3.threshold_get_color(w.get('index'), 'indexage')
                self.py3.threshold_get_color(w.get('pixel'), 'pixelage')
                self.py3.threshold_get_color(w.get('percent'), 'percentage')

            # thresholds for window
            self.py3.threshold_get_color(w.get('index'), 'index')
            self.py3.threshold_get_color(w.get('percent'), 'percent')
            new_window.append(self.py3.safe_format(self.format_window, w))

        # counts for the format
        self.count_floating = count_floating
        self.count_scratchpad = count_scratchpad
        self.count_urgent_window = count_urgent_window
        self.count_urgent_scratchpad = count_urgent_scratchpad
        self.count_window = count_window

        # everything together
        format_separator = self.py3.safe_format(self.format_separator)
        self.fmt_window = self.py3.composite_join(format_separator, new_window)
        self.fmt_scratchpad = self.py3.composite_join(format_separator, new_scratchpad)

        # refresh
        self.py3.update()

    def _switch_window_manipulation(self, direction):
        """
        We don't really switch. We work with mouse events to falsify the data.
        The real event update occurs when the users click and/or leave the bar.
        """
        scratchpads, windows = self.shared_data

        data = {}
        if self._scrolling == 'scratchpad':
            data = scratchpads
        if self._scrolling == 'window':
            data = windows

        if not any(w for w in data if w['is_focused']):
            data[0]['is_focused'] = True

        length = len(data)
        for index, w in enumerate(data):
            if w.get('is_focused'):
                data[index]['is_focused'] = False
                if direction < 0:  # switch previous
                    if index > 0:
                        data[index - 1]['is_focused'] = True
                    else:
                        data[index]['is_focused'] = True
                elif direction > 0:  # switch next
                    if index < (length - 1):
                        data[index + 1]['is_focused'] = True
                    else:
                        data[length - 1]['is_focused'] = True
                break

        if self._scrolling == 'scratchpad':
            scratchpads = data
        if self._scrolling == 'window':
            windows = data

        self._manipulate_and_refresh(scratchpads, windows)

    def window_manipulation(self):
        """
        Return everything. Urgent too if needed.
        """
        response = {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(
                self.format,
                {
                    'class': self.window_class,
                    'floating': self.count_floating,
                    'format_window': self.fmt_window,
                    'format_scratchpad': self.fmt_scratchpad,
                    'id': self.id,
                    'name': self.window_name,
                    'pixel': self.window_pixel,
                    'percent': self.window_percent,
                    'scratchpad': self.count_scratchpad,
                    'urgent_window': self.count_urgent_window,
                    'urgent_scratchpad': self.count_urgent_scratchpad,
                    'window': self.count_window,
                })
        }
        if (self.use_urgent == 'window' and self.count_urgent_window) or (
                self.use_urgent == 'scratchpad' and self.count_urgent_scratchpad):
            response['urgent'] = True
        return response

    def on_click(self, event):
        """
        Users can scroll the windows with mouse, click to focus. If an urgent
        occurs, we will use an urgent click to focus. Disabled by default.
        """
        button = event['button']
        if button == self.button_next:
            self._switch_window_manipulation(+1)
        elif button == self.button_previous:
            self._switch_window_manipulation(-1)
        elif button == self.button_focus:
            if self.count_urgent_window:
                self.py3.command_run('i3-msg "[urgent=latest] focus"')
            else:
                self.py3.command_run('i3-msg "[con_id=%s] focus"' % self.id)
        self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        'format': '[\[W\]: {format_window}][\?soft  ][\[S\]: {format_scratchpad}]',
        'format_window': '\?max_length=5 {name}',
        'format_scratchpad': '\?max_length=5 {name}',
        'format_separator': '/',
        'events': ['window::focus']
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
