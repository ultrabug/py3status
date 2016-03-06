# -*- coding: utf-8 -*-
"""
Group a bunch of modules togeather and switch between them.

In `i3status.conf` groups can be configured. The active one of these groups is
shown in the i3bar.  The active group can be changed by a user click.  If the
click is not used by the group module then it will be passed down to the
displayed module.

Modules can be i3status core modules or py3status modules.

Additionally the active group can be cycled through automatically.

Configuration parameters:
- `button_next` Button that when clicked will switch to display next module.
  Setting to `0` will disable this action. *(default 4)*
- `button_previous` Button that when clicked will switch to display previous
  module.  Setting to `0` will disable this action. *(default 5)*
- `color` If the active module does not supply a color use this if set.
  Format as hex value eg `'#0000FF'` *(default None)*
- `cycle` Time in seconds till changing to next module to display. Setting to
  `0` will disable cycling. *(default 0)*
- `format` Format for module output. *(default "GROUP: {output}")*


Format of status string placeholders:
- `{output}` Output of current active module

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
        format = "/ %avail"
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
    format = "GROUP: {output}"

    def __init__(self):
        self.active = 0
        self._cycle_time = time() + self.cycle

    def _get_current_output(self):
        output = None
        current = self.items[self.active]
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
        return self.items[self.active]

    def _get_current_module(self):
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

    def output(self, i3s_output_list, i3s_config):
        """
        Display a colorful state of DPMS.
        """
        if self.cycle and time() >= self._cycle_time:
            self._next()
            self._cycle_time = time() + self.cycle
        color = None
        current_output = self._get_current_output()
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
        if self.button_next and event['button'] == self.button_next:
            self._next()
        elif self.button_prev and event['button'] == self.button_prev:
            self._prev()
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
    config = {'color_bad': '#FF0000', 'color_good': '#00FF00', }

    while True:
        print(x.dpms([], config))
        sleep(1)
