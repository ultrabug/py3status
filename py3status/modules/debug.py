# -*- coding: utf-8 -*-
"""
Debugging info for loaded modules.

Provides quick and dirty information on loaded modules.
Two screens are provided.  One contains details of running py3status modules.
The other shows the current versions of python, i3 and i3status being used.

Configuration parameters:
    button_next: Button that when clicked will switch to display next module.
        Setting to `0` will disable this action. (default 4)
    button_prev: Button that when clicked will switch to display previous
        module.  Setting to `0` will disable this action. (default 5)
    button_screen: Button that when clicked will change the debug screen
        displayed.  Setting to `0` will disable
        (default 2)
    format: Format for module output.
        (default "{name} {count} {freq}Hz {time} {alive} {cached_until}")
    selected: If set then module of that name will be shown initially
        (default None)


Format of status string placeholders:
    {alive} State of thread `Active` or `Sleeping`
    {cached_until} Time till next update of the module
    {count} Number of updates of module since being monitored
    {freq} Frequency of updates
    {name} Module name
    {time} Time that module has taken running since monitored

@author tobes
@license BSD
"""

from time import time
from collections import deque
import types
import sys
import subprocess
import re


class Py3status:
    # available configuration parameters
    cache_timeout = 0.1
    button_next = 4
    button_prev = 5
    button_screen = 2
    selected = None

    class Meta:
        include_py3_module = True

    def __init__(self):
        self.initialized = False
        self._get_env()

    def _get_env(self):
        output = str(subprocess.check_output(['i3', '-v']))
        i3 = re.search('version\s([0-9.]*)\s', output).group(1)
        output = str(subprocess.check_output(['i3status', '-v']))
        i3status = re.search('\s([0-9.]*)\s', output).group(1)
        self.env = {
            'python': '.'.join(map(str, sys.version_info[:3])),
            'i3': i3,
            'i3status': i3status,
        }

    def _init(self):
        try:
            self.py3_wrapper = self.py3._module._py3_wrapper
        except AttributeError:
            self.py3_wrapper = None
            good = False
        if self.py3_wrapper:
            good = self._patch()
            self.items = self.py3_wrapper.modules
        else:
            self.items = []
        self.active = 0
        if self.selected and self.selected in self.items:
            self.active = self.items.index(self.selected)
        self.initialized = good
        self.format = deque(
                ['{name} {count} {freq}Hz {time} {alive} {cached_until}',
                 'Python v{python}, i3 v{i3}, i3status v{i3status}']
        )
        self.start_time = time()

    def _patch(self):
        # are all the modules loaded yet?  If not try later

        good = len(self.py3_wrapper.modules) == len(self.py3_wrapper.py3_modules)
        if not good:
            return False
        # wrap all the modules run method to allow monitoring
        for module in self.py3_wrapper.modules.values():
            module.debug = {'count': 0, 'time': 0}
            module._run = module.run

            def run(self):
                now = time()
                self.debug['count'] += 1
                self._run()
                self.debug['time'] += time() - now

            module.run = types.MethodType(run, module)
        return True

    def _change_active(self, diff):
        self.active = (self.active + diff) % len(self.py3_wrapper.py3_modules)

    def debug(self):
        """
        Display a output of current module
        """
        if not self.initialized:
            self._init()

        if not self.initialized:
            return {
                'cached_until': time() + 0.1,
                'full_text': ''
            }
        name = self.py3_wrapper.py3_modules[self.active]
        module = self.py3_wrapper.modules[name]
        count = module.debug['count']
        if count:
            freq = '{0:.2f}'.format((time() - self.start_time)/count)
        else:
            freq = '?'
        _time = '{0:.3f}'.format(module.debug['time'])
        if module.timer and module.timer.is_alive():
            alive = 'Active'
        else:
            alive = 'Sleeping'
        if module.cache_time:
            cached_until = module.cache_time - time()
        else:
            cached_until = 0
        if cached_until <= 0.001:
            cached_until = 0
        cached_until = '{0:.2f}'.format(cached_until)

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': self.format[0].format(name=name,
                                               count=count,
                                               freq=freq,
                                               time=_time,
                                               alive=alive,
                                               cached_until=cached_until,
                                               **self.env)
        }
        return response

    def on_click(self, event):
        """
        Switch the displayed module or pass the event on to the active module
        """
        button = event['button']

        if self.button_next and button == self.button_next:
            self._change_active(1)
        elif self.button_prev and button == self.button_prev:
            self._change_active(-1)
        elif self.button_screen and button == self.button_screen:
            self.format.rotate()


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {}

    while True:
        print(x.debug([], config))
        sleep(1)
