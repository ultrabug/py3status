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
        py3_wrapper = self.py3_wrapper
        if current in py3_wrapper.output_modules:
            output = py3_wrapper.output_modules[current]['module'].get_latest()[0]
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

        # hide if no contents
        # FIXME the module shouldn't even run if no content
        if not self.items:
            return {
                'cached_until': time() + 36000,
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
        update_time = self.cycle or 1000

        # on the first run contained items may not be displayed so make sure we
        # check them again to ensure all is correct
        if not ready:
            update_time = 0.1

        response = {
            'cached_until': time() + update_time,
            'full_text': self.format.format(output=output)
        }
        if color:
            response['color'] = color
        elif self.color:
            response['color'] = self.color
        return response

    def _call_i3status_config_on_click(self, module_name, event):
        """
        call any on_click event set in the config for the named module
        """
        config = self.py3_module.py3_wrapper.i3status_thread.config[
            'on_click']
        click_info = config.get(module_name, None)
        if click_info:
            action = click_info.get(event['button'])
            if action:
                # we have an action so call it
                self.py3_module.py3_wrapper.events_thread.i3_msg(
                    module_name, action)

    def on_click(self, i3s_output_list, i3s_config, event):
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

        # any event set in the config for the group
        name = self.py3_module.module_full_name
        self._call_i3status_config_on_click(name, event)

        # any event set in the config for the active module
        current_module = self.items[self.active]
        self._call_i3status_config_on_click(current_module, event)

        # try the modules own click event
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
