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
    format: Format for module output. (default "GROUP: {output}")


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
    format = "GROUP: {output}"

    class Meta:
        include_py3_module = True

    def __init__(self):
        self.items = []
        self.active = 0
        self.initialized = False

    def _init(self):
        try:
            self.py3_wrapper = self.py3_module.py3_wrapper
        except AttributeError:
            self.py3_wrapper = None

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
        width = max(widths)
        current['full_text'] += ' ' * (width - len(current['full_text']))
        return current

    def _get_current_output(self, item):
        output = None
        current = self.items[item]
        py3_wrapper = self.py3_wrapper
        if current in py3_wrapper.modules:
            for method in py3_wrapper.modules[current].methods.values():
                output = method['last_output']
        else:
            if py3_wrapper.i3status_thread.config.get(current,
                                                      {}).get('response'):
                output = (
                    py3_wrapper.i3status_thread.config[current]['response'])
        return output

    def _get_current_module_name(self):
        if not self.items:
            return
        return self.items[self.active]

    def _get_current_module(self):
        if not self.items:
            return
        current = self.items[self.active]
        py3_wrapper = self.py3_wrapper
        if current in py3_wrapper.modules:
            return py3_wrapper.modules[current]
        else:
            return py3_wrapper.config.get(current)

    def _next(self):
        self.active = (self.active + 1) % len(self.items)

    def _prev(self):
        self.active = (self.active - 1) % len(self.items)

    def group(self, i3s_output_list, i3s_config):
        """
        Display a output of current module
        """
        if not self.initialized:
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
        update_time = self.cycle or 1000
        response = {
            'cached_until': time() + update_time,
            'full_text': self.format.format(output=output)
        }
        if color:
            response['color'] = color
        elif self.color:
            response['color'] = self.color
        return response

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Switch the displayed module or pass the event on to the active module
        """
        if not self.items:
            return
        if self.button_next and event['button'] == self.button_next:
            self._next()
            self._cycle_time = time() + self.cycle
        elif self.button_prev and event['button'] == self.button_prev:
            self._prev()
            self._cycle_time = time() + self.cycle
        else:
            self._cycle_time = time() + self.cycle
            current_module = self._get_current_module()
            current_module.click_event(event)
            self.py3_wrapper.events_thread.refresh(
                current_module.module_full_name)


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
