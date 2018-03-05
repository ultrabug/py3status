# -*- coding: utf-8 -*-
"""
Support i3pystatus modules in py3status.

[i3pystatus](https://github.com/enkore/i3pystatus) is an alternative to
py3status and provides a variety of modules.  This py3status module allows
these modules to run and be display inside py3status.

The modules parameters are provided as such
```
i3pystatus clock {
    module = 'clock'
    format = [ ('%a %b %-d %b %X', 'America/New_York'), ('%X', 'Etc/GMT+9') ]
}
```

if backend(s) are provided they should be given as a dict with the key being
the backend name and the value being a dict of the backend settings

```
i3pystatus weather {
    module = 'weather'
    format = '{condition} {current_temp}{temp_unit}[ {icon}]'
    format += '[ Hi: {high_temp}][ Lo: {low_temp}][ {update_error}]'
    backend = {
        'weathercom.Weathercom': {
            'location_code': '94107:4:US',
            'units': 'imperial',
        }
    }
}
```

backends that have no configuration should be defined as shown here

```
i3pystatus updates{
    module = 'updates'
    backends = {'dnf.Dnf': {}}
}
```

Configuration parameters:
    module: name of the i3pystatus module (default None)

    (additional parameters as per the i3pystatus module)

Requires:
    i3pystatus: i3status replacement written in python

@author tobes
"""

import os

from importlib import import_module
from threading import Timer

try:
    import i3pystatus
except ImportError:
    i3pystatus = None


MIN_CHECK_INTERVAL = 15  # the minimum time between checking the modules output
MAX_AUTO_TIMEOUT = 30  # the longest we'll leave it without checking the output

CLICK_EVENTS = [
    'on_leftclick',
    'on_middleclick',
    'on_rightclick',
    'on_upscroll',
    'on_downscroll',

    'on_unhandledclick',
]

DBL_CLICK_EVENTS = [
    'on_doubleleftclick',
    'on_doublemiddleclick',
    'on_doublerightclick',
    'on_doubleupscroll',
    'on_doubledownscroll',

    'on_doubleunhandledclick',
]

# we can only have one status running ever
status = None
backends = None


def get_backends():
    """
    Get backends info so that we can find the correct one.
    We just look in the directory structure to find modules.
    """
    IGNORE_DIRS = ['core', 'tools', 'utils']

    global backends
    if backends is None:
        backends = {}
        i3pystatus_dir = os.path.dirname(i3pystatus.__file__)
        subdirs = [x for x in next(os.walk(i3pystatus_dir))[1]
                   if not x.startswith('_') and x not in IGNORE_DIRS]
        for subdir in subdirs:
            dirs = next(os.walk(os.path.join(i3pystatus_dir, subdir)))[2]
            backends.update(
                {x[:-3]: 'i3pystatus.%s.%s' % (subdir, x[:-3])
                 for x in dirs if not x.startswith('_') and x.endswith('.py')}
            )
    return backends


class ClickTimer:
    """
    i3pystatus support double clicks that py3status does not
    therefore we have to add this functionality.

    Although double clicks are a simple concept double clicks on the mouse
    wheel do not make much sense as when we are scrolling it could easily be
    interpreted as multiple double clicks.  For this reason we only worry about
    double clicks if the mouse button has a double click event.  If it dies not
    then we just count the click as a single click. more than 2 clicks are also
    viewed as a double click.

    Additionally all buttons 6 and more use the unhandled click event but each
    button is treated independently.
    """

    def __init__(self, parent, callbacks):
        self.callbacks = callbacks
        self.parent = parent
        self.last_button = None
        self.clicks = 0
        self.click_time = getattr(
            self.parent.module, 'multi_click_timeout', 0.25
        )
        self.timer = None

    def trigger(self):
        """
        Actually trigger the event
        """
        if self.last_button:
            button_index = min(self.last_button, len(self.callbacks)) - 1
            click_style = 0 if self.clicks == 1 else 1
            callback = self.callbacks[button_index][click_style]
            if callback:
                # we can do test for str as only python > 3 is supported
                if isinstance(callback, str):
                    # no parameters
                    callback_name = callback
                    callback_args = []
                else:
                    # has parameters
                    callback_name = callback[0]
                    callback_args = callback[1:]
                callback_function = getattr(self.parent.module, callback_name)
                callback_function(*callback_args)
                # We want to ensure that the module has the latest output.  The
                # best way is to call the run method of the module
                self.parent.module.run()
            else:
                self.parent.py3.prevent_refresh()
        self.last_button = None
        self.clicks = 0

    def event(self, button):
        """
        button has been clicked
        """
        # cancel any pending timer
        if self.timer:
            self.timer.cancel()
        if self.last_button != button:
            if self.last_button:
                # new button clicked process the one before.
                self.trigger()
            self.clicks = 1
        else:
            self.clicks += 1
        # do we accept double clicks on this button?
        # if not then just process the click
        button_index = min(button, len(self.callbacks)) - 1
        if not self.callbacks[button_index][1]:
            # set things up correctly for the trigger
            self.clicks = 1
            self.last_button = button
            self.trigger()
        else:
            # set a timeout to trigger the click
            # this will be cancelled if we click again before it runs
            self.last_button = button
            self.timer = Timer(self.click_time, self.trigger)
            self.timer.start()


SKIP_ATTRS = [
    'on_click',
    'run',
    'post_config_hook',
    'module',
    'py3',
]


class Py3status:
    """
    """

    module = None

    def post_config_hook(self):
        if i3pystatus is None:
            raise Exception('i3pystatus is not installed')

        if self.py3.is_python_2():
            raise Exception('Python 2 not supported by i3pystatus :(')

        if not self.module:
            raise Exception('No module selected')

        settings = {}
        for attribute in dir(self):
            if attribute.startswith('__') or attribute in SKIP_ATTRS:
                continue
            settings[attribute] = getattr(self, attribute)

        # backends
        backend_type = None
        if 'backend' in settings:
            backend_type = 'backend'
        elif 'backends' in settings:
            backend_type = 'backends'

        if backend_type:
            backends = settings[backend_type]
            backends_initiated = []
            for key, value in backends.items():
                mod_info = key.split('.')
                backend_module = import_module(get_backends().get(mod_info[0]))
                try:
                    backend = getattr(backend_module, mod_info[1])(**value)
                except i3pystatus.core.exceptions.ConfigMissingError as e:
                    msg = e.message
                    msg = (
                        'i3pystatus module `{}` backend `{}`'
                        'missing configuration options {}'
                    ).format(
                        self.module, key, msg[msg.index('{'):]
                    )
                    self.py3.notify_user(msg)
                    raise Exception('Missing configuration options')
                backends_initiated.append(backend)
            if backend_type == 'backend':
                settings['backend'] = backends_initiated[0]
            else:
                settings['backends'] = backends_initiated

        # i3pystatus.Status can only exist once
        # so create it and share
        global status

        if status is None:
            status = i3pystatus.Status()

        # create the module and register it
        finder = status.modules.finder
        try:
            module = finder.instanciate_class_from_module(self.module, **settings)
        except i3pystatus.core.exceptions.ConfigMissingError as e:
            msg = e.message
            msg = 'i3pystatus module `{}` missing configuration options {}'.format(
                self.module, msg[msg.index('{'):]
            )
            self.py3.notify_user(msg)
            raise Exception('Missing configuration options')
        status.register(module)
        self.module = module

        self.is_interval_module = isinstance(module, i3pystatus.IntervalModule)
        # modules update their output independently so we need to periodically
        # check if it has been updated.  For modules with long intervals it is
        # important to do this output check much more regularly thank the
        # interval.
        self._cache_timeout = min(
            getattr(module, 'interval', MIN_CHECK_INTERVAL), MIN_CHECK_INTERVAL
        )

        # get callbacks available, useful for deciding if double clicks exist
        callbacks = []
        for i in range(len(CLICK_EVENTS)):
            click = getattr(module, CLICK_EVENTS[i], None)
            dbclick = getattr(module, DBL_CLICK_EVENTS[i], None)
            callbacks.append((click, dbclick))

        self._click_timer = ClickTimer(self, callbacks)
        self._last_content = None
        self._timeout = 1

    def run(self):
        output = self.module.output or {'full_text': ''}

        if self._last_content != output:
            self._last_content = output
            self._timeout = 1
        else:
            self._timeout *= 2
            if self._timeout > MAX_AUTO_TIMEOUT:
                self._timeout = MAX_AUTO_TIMEOUT

        # some modules return tuples
        if isinstance(output['full_text'], tuple):
            output['full_text'] = output['full_text'][0]

        if self.is_interval_module:
            output['cached_until'] = self.py3.time_in(
                sync_to=min(self._cache_timeout, self._timeout)
            )
        else:
            output['cached_until'] = self.py3.time_in(
                sync_to=self._timeout
            )

        return output

    def on_click(self, event):
        self._click_timer.event(event['button'])
