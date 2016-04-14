# -*- coding: utf-8 -*-
"""
Group a bunch of modules together and switch between them.

In `i3status.conf` groups can be configured. The active one of these groups is
shown in the i3bar.  The active group can be changed by a user click.  If the
click is not used by the group module then it will be passed down to the
displayed module.

Modules can be i3status core modules or py3status modules.

Additionally the active group can be cycled through automatically.

Configuration parameters:
    button_next: Button that when clicked will switch to display next module.
        Setting to `0` will disable this action. (default 4)
    button_prev: Button that when clicked will switch to display previous
        module.  Setting to `0` will disable this action. (default 5)
    color: If the active module does not supply a color use this if set.
        Format as hex value eg `'#0000FF'` (default None)
    cycle: Time in seconds till changing to next module to display.
        Setting to `0` will disable cycling. (default 0)
    fixed_width: Reduce the size changes when switching to new group
        (default True)
    format: Format for module output. (default "{output}")


Format of status string placeholders:
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
    format = "Disks: {output}"

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

from time import time


class Py3status:
    # available configuration parameters
    button_next = 4
    button_prev = 5
    color = None
    cycle = 0
    fixed_width = True
    format = u'{output}'

    class Meta:
        container = True

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

    def _get_output(self):
        if not self.items:
            return
        if not self.fixed_width:
            return self._get_current_output(self.active)
        current = None
        widths = []
        for i in range(len(self.items)):
            output = self._get_current_output(i)
            if not output:
                continue
            if i == self.active:
                current = output
            widths.append(len(output['full_text']))
        if widths:
            width = max(widths)
            current['full_text'] += ' ' * (width - len(current['full_text']))
        return current

    def _get_current_output(self, item):
        output = None
        current = self.items[item]
        module_info = self.py3.get_module_info(current)
        if module_info:
            output = module_info['module'].get_latest()[0]
        return output

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

        if self.cycle and time() >= self._cycle_time:
            self._next()
            self._cycle_time = time() + self.cycle
        output = '?'
        color = None
        current_output = self._get_output()

        if current_output:
            output = current_output['full_text']
            color = current_output.get('color')
        update_time = self.cycle or None

        # FIXME always start contained items after container so they trigger
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
            'full_text': self.format.format(output=output)
        }
        if color:
            response['color'] = color
        elif self.color:
            response['color'] = self.color
        return response

    def on_click(self, event):
        """
        Switch the displayed module or pass the event on to the active module
        """
        if not self.items:
            return
        # reset cycle time
        self._cycle_time = time() + self.cycle
        if self.button_next and event['button'] == self.button_next:
            self._next()
        if self.button_prev and event['button'] == self.button_prev:
            self._prev()

        # pass the event to the current module
        module_name = self._get_current_module_name()
        self.py3.trigger_event(module_name, event)


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
