Writing custom py3status modules
================================

__This guide covers the new style of py3status modules.  These are only
available in version 3.0 and above__

Writing custom modules for py3status is easy.  This guide will teach you how.

Let's start by looking at a simple example.

##Example 1:  The basics - Hello World!

Here we start with the most basic module that just outputs a static string to
the status bar.

```
# -*- coding: utf-8 -*-
"""
Example module that says 'Hello World!'

This demonstrates how to produce a simple custom module.
"""


class Py3status:

    def hello_world(self):
        return {
            'full_text': 'Hello World!',
            'cache_until': self.py3.CACHE_FOREVER
        }
```

####Running the example


Save the file as `hello_world.py` in a directory that
py3status will check for modules. By default it will look in
`$HOME/.i3/py3status/` or you can specify additional directories using
`--include` when you run py3status.

You need to tell py3status about your new module so in your `i3status.conf` add
```
order += "hello_world"
```

Then restart i3 by pressing `Mod` + `Shift` + `R`.  Your new module should now
show up in the status bar.

####How does it work?

The `Py3status` class tell py3status that this is a module.  The module gets
loaded.  py3status then calls any public methods that the class contains to get
a response.  In our example there is a single method `hello_world()`.

####The response

The response that a method returns must be a python `dict`.
It should contain at least two key / values.

######full_text

This is the text that will be displayed in the status bar.

######cache_until

This tells py3status how long it should consider your
response valid before it should re-run the method to get a fresh response.  In
our example our response will not need to be updated so we can use the special
`self.py3.CACHE_FOREVER` constant.  This tells py3status to consider our
response always valid.

####self.py3

This is a special object that gets injected into Py3status
modules.  It helps provide functionality for the module, such as the
`CACHE_FOREVER` constant.


## Example 2: Configuration parameters

Allow users to supply configuration to a module.

```
# -*- coding: utf-8 -*-
"""
Example module that says 'Hello World!' that can be customised.

This demonstrates how to use configuration parameters.

Configuration parameters:
    format: Display format (default 'Hello World!')
"""


class Py3status:

    format = 'Hello World!'

    def hello_world(self):
        return {
            'full_text': self.format,
            'cache_until': self.py3.CACHE_FOREVER
        }
```
This module still outputs 'Hello World' as before but now you can customise the
output using your `i3status.config` for example to show the text in French.
```
hello_world {
    format = 'Bonjour le monde'
}
```
In your module `self.format` will have been set to the value supplied in the
config.


## Example 3: Events

Catch click events and perform an action.

```
# -*- coding: utf-8 -*-
"""
Example module that handles events

This demonstrates how to use events.
"""


class Py3status:

    def __init__(self):
        self.full_text = 'Click me'

    def click_info(self):
        return {
            'full_text': self.full_text,
            'cache_until': self.py3.CACHE_FOREVER
        }

    def on_click(self, event):
        """
        event will be a dict like
        {'y': 13, 'x': 1737, 'button': 1, 'name': 'example', 'instance': 'first'}
        """
        button = event['button']
        self.full_text = 'You pressed button {}'.format(button)
        # Our modules update methods will get called automatically.
```

The `on_click` method of a module is special and will get
called when the module is clicked on.  The event parameter
will be a dict that gives information about the event. A
typical event dict will look like `{'y': 13, 'x': 1737,
'button': 1, 'name': 'example', 'instance': 'first'}` you
should only receive events for the module clicked on, so
generally we only care about the button.

The `__init__()` method is called when our class is instantiated.  __Note: this
is called before any config parameters have been set__

## Example 4: Status string placeholders

Status string placeholders allow us to add information to formats.


```
# -*- coding: utf-8 -*-
"""
Example module that demonstrates status string placeholders

Configuration parameters:
    format: Initial format to use
        (default 'Click me')
    format_clicked: Display format to use when we are clicked
        (default 'You pressed button {button}')

Format status string parameters:
    {button} The button that was pressed
"""


class Py3status:
    format = 'Click me'
    format_clicked = 'You pressed button {button}'

    def __init__(self):
        self.button = None

    def click_info(self):
        if self.button:
            full_text = self.format_clicked.format(button=self.button)
        else:
            full_text = self.format

        return {
            'full_text': full_text,
            'cache_until': self.py3.CACHE_FOREVER
        }

    def on_click(self, event):
        """
        event will be a dict like
        {'y': 13, 'x': 1737, 'button': 1, 'name': 'example', 'instance': 'first'}
        """
        self.button = event['button']
        # Our modules update methods will get called automatically.
```

This works just like the previous example but we can now be customised.  The
following example assumes that out module has been saved as `click_info.py`.

```
click_info {
    format = "Cliquez ici"
    format_clicked = "Vous bouton {button} enfoncé"
}
```
