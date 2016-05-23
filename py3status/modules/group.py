# -*- coding: utf-8 -*-
"""
Group a bunch of modules together and switch between them.

In `i3status.conf` groups can be configured. The active one of these groups is
shown in the i3bar.  The active group can be changed by a user click.  If the
click is not used by the group module then it will be passed down to the
displayed module.

Modules can be i3status core modules or py3status modules.  The active group
can be cycled through automatically.

The group can handle clicks by reacting to any that are made on it or its
content or it can use a button and only respond to clicks on that.
The way it does this is selected via the `click_mode` option.

Configuration parameters:
    align: Text alignment when fixed_width is set
        can be 'left', 'center' or 'right' (default 'center')
    button_next: Button that when clicked will switch to display next module.
        Setting to `0` will disable this action. (default 5)
    button_prev: Button that when clicked will switch to display previous
        module.  Setting to `0` will disable this action. (default 4)
    button_toggle: Button that when clicked toggles the group content being
        displayed between open and closed.
        This action is ignored if `{button}` is not in the format.
        Setting to `0` will disable this action (default 1)
    click_mode: This defines how clicks are handled by the group.
        If set to `all` then the group will respond to all click events.  This
        may cause issues with contained modules that use the same clicks that
        the group captures.  If set to `button` then only clicks that are
        directly on the `{button}` are acted on.  The group
        will need `{button}` in its format.
        (default 'all')
    cycle: Time in seconds till changing to next module to display.
        Setting to `0` will disable cycling. (default 0)
    fixed_width: Reduce the size changes when switching to new group
        (default False)
    format: Format for module output.
        (default "{output}" if click_mode is 'all',
        "{output} {button}" if click_mode 'button')
    format_button_open: Format for the button when group closed
        (default '+')
    format_button_closed: Format for the button when group open
        (default  '-')
    format_closed: Format for module output when closed.
        (default "{button}")
    open: Is the group open and displaying its content. Has no effect if
        `{button}` not in format (default True)


Format of status string placeholders:
    {button} The button to open/close or change the displayed group
    {output} Output of current active module

Example:

```
# Create a disks group that will show space on '/' and '/home'
# Change between disk modules every 30 seconds
...
order += "group disks"
...

group disks {
    cycle = 30
    format = "Disks: {output} {button}"
    click_mode = "button"

    disk "/" {
        format = "/ %avail"
    }

    disk "/home" {
        format = "/home %avail"
    }
}
```

@author tobes
"""

from re import findall
from time import time


class Py3status:
    # available configuration parameters
    align = 'center'
    button_next = 5
    button_prev = 4
    button_toggle = 1
    click_mode = 'all'
    cycle = 0
    fixed_width = False
    format = None
    format_button_open = u'-'
    format_button_closed = u'+'
    format_closed = u'{button}'
    open = True

    def __init__(self):
        self.items = []
        self.active = 0
        self.initialized = False

    def _init(self):
        # if no items don't cycle
        if not self.items:
            self.cycle = 0
        self._cycle_time = time() + self.cycle
        self.initialized = True
        self.open = bool(self.open)
        # set default format etc based on click_mode
        if self.format is None:
            if self.click_mode == 'button':
                self.format = u'{output} {button}'
            else:
                self.format = u'{output}'
        # if no button then force open
        if '{button}' not in self.format:
                self.open = True

    def _get_output(self):
        if not self.fixed_width:
            return self.py3.get_output(self.items[self.active])
        # fixed width we need to find the width of all outputs
        # and then pad with spaces to make correct width.
        current = []
        widths = []
        for i in range(len(self.items)):
            output = self.py3.get_output(self.items[i])
            if not output:
                continue
            widths.append(sum([len(x['full_text']) for x in output]))
            if i == self.active:
                current = output
                current_width = widths[-1]
        if widths:
            width = max(widths)
            padding = ' ' * (width - current_width)
            if self.align == 'right':
                current[0]['full_text'] = padding + current[0]['full_text']
            elif self.align == 'center':
                cut = len(padding) // 2
                current[0]['full_text'] = padding[:cut] + \
                    current[0]['full_text']
                current[-1]['full_text'] += padding[cut:]
            else:
                current[-1]['full_text'] += padding
        return current

    def _get_current_module_name(self):
        if not self.items:
            return
        return self.items[self.active]

    def _next(self):
        self.active = (self.active + 1) % len(self.items)

    def _prev(self):
        self.active = (self.active - 1) % len(self.items)

    def group(self):
        """
        Display a output of current module
        """

        # hide if no contents
        # FIXME the module shouldn't even run if no content
        if not self.items:
            return {
                'cached_until': self.py3.CACHE_FOREVER,
                'full_text': '',
            }

        ready = self.initialized
        if not ready:
            self._init()

        if self.open:
            if self.cycle and time() >= self._cycle_time:
                self._next()
                self._cycle_time = time() + self.cycle
            current_output = self._get_output()
            update_time = self.cycle or None
        else:
            current_output = []
            update_time = None

        if self.open:
            format_control = self.format_button_open
            format = self.format
        else:
            format_control = self.format_button_closed
            format = self.format_closed

        parts = findall('({[^}]*}|[^{]+)', format)

        output = []
        for part in parts:
            if part == '{output}':
                output += current_output
            elif part == '{button}':
                output += [{'full_text': format_control,
                            'index': 'button'}]
            else:
                output += [{'full_text': part}]

        # on the first run contained items may not be displayed so make sure we
        # check them again to ensure all is correct
        if not ready:
            update_time = 0

        if update_time is not None:
            cached_until = time() + update_time
        else:
            cached_until = self.py3.CACHE_FOREVER

        response = {
            'cached_until': cached_until,
            'composite': output
        }
        return response

    def on_click(self, event):
        """
        Switch the displayed module or pass the event on to the active module
        """
        if not self.items:
            return

        # if click_mode is button then we only action clicks that are
        # directly on the group not its contents.
        if self.click_mode == 'button':
            if event['name'] != 'group' or event.get('index') != 'button':
                return

        # reset cycle time
        self._cycle_time = time() + self.cycle
        if self.button_next and event['button'] == self.button_next:
            self._next()
        if self.button_prev and event['button'] == self.button_prev:
            self._prev()
        if self.button_toggle and event['button'] == self.button_toggle:
            # we only toggle if button was used
            if event.get('index') == 'button':
                self.open = not self.open


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {}

    while True:
        print(x.group([], config))
        sleep(1)
