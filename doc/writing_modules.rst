Writing custom py3status modules
================================

.. note::
    This guide covers the new style of py3status modules. These are only
    available in version 3.0 and above.

Writing custom modules for py3status is easy. This guide will teach you how.

Importing custom modules
------------------------

py3status will try to find custom modules in the following locations:

- ``~/.config/py3status/modules``
- ``~/.config/i3status/py3status``
- ``~/.config/i3/py3status``
- ``~/.i3/py3status``

which if you are used to XDG_CONFIG paths relates to:

- ``XDG_CONFIG_HOME/py3status/modules``
- ``XDG_CONFIG_HOME/i3status/py3status``
- ``XDG_CONFIG_HOME/i3/py3status``
- ``~/.i3/py3status``

You can also specify the modules location using ``py3status -i <path to custom
modules directory>`` in your i3 configuration file.

Publishing custom modules on PyPI
---------------------------------

.. note::
    Available since py3status version 3.20.

You can share your custom modules and make them available for py3status users even
if they are not directly part of the py3status main project!

All you have to do is to package your module and publish it to PyPI.

py3status will discover custom modules if they are installed in the same host
interpreter and if an entry_point in your package ``setup.py`` is defined::

    setup(
        entry_points={"py3status": ["module = package_name.py3status_module_name"]},
    )

The awesome `pewpew` module can be taken as an example on how to do it easily:

- Module repository: https://github.com/obestwalter/py3status-pewpew
- Example setup.py: https://github.com/obestwalter/py3status-pewpew/blob/master/setup.py

We will gladly add ``extra_requires`` pointing to your modules so that users can require
them while installing py3status. Just open an issue to request this or propose a PR.

If you have installed py3status in a virtualenv (maybe because your custom module
has dependencies that need to be available) you can also create an installable
package from your module and publish it on PyPI.

.. note::
    To clearly identify your py3status package and for others to discover it easily
    it is recommended to name the PyPI package ``py3status-<your module name>``.

Example 1: The basics - Hello World!
------------------------------------

Now let's start by looking at a simple example.

Here we start with the most basic module that just outputs a static string to
the status bar.

.. code-block:: python

    # -*- coding: utf-8 -*-
    """
    Example module that says 'Hello World!'

    This demonstrates how to produce a simple custom module.
    """


    class Py3status:

        def hello_world(self):
            return {
                'full_text': 'Hello World!',
                'cached_until': self.py3.CACHE_FOREVER
            }

Running the example
^^^^^^^^^^^^^^^^^^^


Save the file as ``hello_world.py`` in a directory that
py3status will check for modules. By default it will look in
``$HOME/.i3/py3status/`` or you can specify additional directories using
``--include`` when you run py3status.

You need to tell py3status about your new module,
so in your ``i3status.conf`` add:

.. code-block:: none

    order += "hello_world"

Then restart i3 by pressing ``Mod`` + ``Shift`` + ``R``. Your new module should now
show up in the status bar.

How does it work?
^^^^^^^^^^^^^^^^^

The ``Py3status`` class tells py3status that this is a module. The module gets
loaded. py3status then calls any public methods that the class contains to get
a response. In our example there is a single method ``hello_world()``.
Read more here: [module methods](#module_methods).

The response
^^^^^^^^^^^^

The response that a method returns must be a python ``dict``.
It should contain at least two key / values.

full_text
^^^^^^^^^

This is the text that will be displayed in the status bar.

cached_until
^^^^^^^^^^^^

This tells py3status how long it should consider your
response valid before it should re-run the method to get a fresh response. In
our example our response will not need to be updated so we can use the special
``self.py3.CACHE_FOREVER`` constant. This tells py3status to consider our
response always valid.

``cached_until`` should be generated via the ``self.py3.time_in()`` method.

self.py3
^^^^^^^^

This is a special object that gets injected into py3status
modules. It helps provide functionality for the module, such as the
``CACHE_FOREVER`` constant. Read more about the :ref:`py3`.


Example 2: Configuration parameters
-----------------------------------

Allow users to supply configuration to a module.

.. code-block:: python

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
                'cached_until': self.py3.CACHE_FOREVER
            }

This module still outputs 'Hello World' as before but now you can customise the
output using your ``i3status.config`` for example to show the text in French.

.. code-block:: none

    hello_world {
        format = 'Bonjour tout le monde!'
    }

In your module ``self.format`` will have been set to the value supplied in the
config.


Example 3: Click events
-----------------------

Catch click events and perform an action.

.. code-block:: python

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
                'cached_until': self.py3.CACHE_FOREVER
            }

        def on_click(self, event):
            """
            event will be a dict like
            {'y': 13, 'x': 1737, 'button': 1, 'name': 'example', 'instance': 'first'}
            """
            button = event['button']
            # update our output (self.full_text)
            format_string = 'You pressed button {button}'
            data = {'button': button}
            self.full_text = self.py3.safe_format(format_string, data)
            # Our modules update methods will get called automatically.

The ``on_click`` method of a module is special and will get
called when the module is clicked on. The event parameter
will be a dict that gives information about the event.

A typical event dict will look like this:
``{'y': 13, 'x': 1737, 'button': 1, 'name': 'example', 'instance': 'first'}``

You should only receive events for the module clicked on, so
generally we only care about the button.

The ``__init__()`` method is called when our class is instantiated.

.. note::
    __init__ is called before any config parameters have been set.

We use the ``safe_format()`` method of ``py3`` for formatting. Read more about
the :ref:`py3`.

Example 4: Status string placeholders
-------------------------------------

Status string placeholders allow us to add information to formats.


.. code-block:: python

    # -*- coding: utf-8 -*-
    """
    Example module that demonstrates status string placeholders

    Configuration parameters:
        format: Initial format to use
            (default 'Click me')
        format_clicked: Display format to use when we are clicked
            (default 'You pressed button {button}')

    Format placeholders:
        {button} The button that was pressed
    """


    class Py3status:
        format = 'Click me'
        format_clicked = 'You pressed button {button}'

        def __init__(self):
            self.button = None

        def click_info(self):
            if self.button:
                data = {'button': self.button}
                full_text = self.py3.safe_format(self.format_clicked, data)
            else:
                full_text = self.format

            return {
                'full_text': full_text,
                'cached_until': self.py3.CACHE_FOREVER
            }

        def on_click(self, event):
            """
            event will be a dict like
            {'y': 13, 'x': 1737, 'button': 1, 'name': 'example', 'instance': 'first'}
            """
            self.button = event['button']
            # Our modules update methods will get called automatically.

This works just like the previous example but we can now be customised. The
following example assumes that our module has been saved as `click_info.py`.

.. code-block:: none

    click_info {
        format = "Cliquez ici"
        format_clicked = "Vous avez appuyé sur le bouton {button}"
    }

Example 5: Using color constants
--------------------------------

``self.py3`` in our module has color constants that we can access, these allow the user to set colors easily in their config.

.. note::
    py3 colors constants require py3status 3.1 or higher


.. code-block:: python

    # -*- coding: utf-8 -*-
    """
    Example module that uses colors.

    We generate a random number between and color it depending on its value.
    Clicking on the module will update it an a new number will be chosen.

    Configuration parameters:
        format: Initial format to use
            (default 'Number {number}')

    Format placeholders:
        {number} Our random number

    Color options:
        color_high: number is 5 or higher
        color_low: number is less than 5
    """

    from random import randint


    class Py3status:
        format = 'Number {number}'

        def random(self):
            number = randint(0, 9)
            full_text = self.py3.safe_format(self.format, {'number': number})

            if number < 5:
                color = self.py3.COLOR_LOW
            else:
                color = self.py3.COLOR_HIGH

            return {
                'full_text': full_text,
                'color': color,
                'cached_until': self.py3.CACHE_FOREVER
            }

        def on_click(self, event):
            # by defining on_click pressing any mouse button will refresh the
            # module.
            pass

The colors can be set in the config in the module or its container or in the
general section.  The following example assumes that our module has been saved
as ``number.py``.  Although the constants are capitalized they are defined in the
config in lower case.

.. code-block:: none

    number {
        color_high = '#FF0000'
        color_low = '#00FF00'
    }


Module methods
--------------

Py3status will call a method in a module to provide output to the i3bar.
Methods that have names starting with an underscore will not be used in this
way.  Any methods defined as static methods will also not be used.

Outputs
^^^^^^^

Output methods should provide a response dict.

Example response:

.. code-block:: python

    {
        'full_text': "This text will be displayed",
        'cached_until': 1470922537,  # Time in seconds since the epoch
    }

The response can include the following keys

**cached_until**

The time (in seconds since the epoch) that the output will be classed as no longer valid and the output
function will be called again.

Since version 3.1, if no ``cached_until`` value is provided the output will
be cached for ``cache_timeout`` seconds by default this is ``60`` and can be
set using the ``-t`` or ``--timeout`` option when running py3status.  To never
expire the ``self.py3.CACHE_FOREVER`` constant should be used.

``cached_until`` should be generated via the ``self.py3.time_in()`` method.

**color**

The color that the module output will be displayed in.

**composite**

Used to output more than one item to i3bar from a single output method.  If this is provided then ``full_text`` should not be.

**full_text**

This is the text output that will be sent to i3bar.

**index**

The index of the output.  Allows composite output to identify which component
of their output had an event triggered.

**separator**

If ``False`` no separator will be shown after the output block (requires i3bar
4.12).

**urgent**

If ``True`` the output will be shown as urgent in i3bar.


Special methods
^^^^^^^^^^^^^^^

Some special method are also defined.

**kill()**

Called just before a module is destroyed.

**on_click(event)**

Called when an event is received by a module.

**post_config_hook()**

Called once an instance of a module has been created and the configuration
parameters have been set.  This is useful for any work a module must do before
its output methods are run for the first time. ``post_config_hook()``
introduced in version 3.1


Py3 module helper
-----------------

Py3 is a special helper object that gets injected into
py3status modules, providing extra functionality.
A module can access it via the self.py3 instance attribute
of its py3status class. For details see :ref:`py3`.


Composites
----------

Whilst most modules return a simple response eg:

.. code-block:: python

    {
        'full_text': <some text>,
        'cached_until': <cache time>,
    }

Sometimes it is useful to provide a more complex, composite response.  A
composite is made up of more than one simple response which allows for example
a response that has multiple colors.  Different parts of the response can also
be differentiated between when a click event occurs and so allow clicking on
different parts of the response to have different outcomes.  The different
parts of the composite will not have separators between them in the output so
they will appear as a single module to the user.

The format of a composite is as follows:

.. code-block:: python

    {
        'cached_until': <cache time>,
        'composite': [
            {
                'full_text': <some text>,
            },
            {
                'full_text': <some more text>,
                'index': <some index>
            },
        ]
    }

The ``index`` key in the response is used to identify the individual block and
when the modules ``on_click()`` method is called the event will include this.
Supplied index values should be strings.  If no index is given then it will
have an integer value indicating its position in the composite.


Module data storage
-------------------

Py3status allows modules to maintain state through the use of the storage
functions of the Py3 helper.

Currently bool, int, float, None, unicode, dicts, lists, datetimes etc are
supported.  Basically anything that can be pickled.  We do our best to ensure
that the resulting pickles are compatible with both python versions 2 and 3.

The following helper functions are defined in the modules :ref:`py3`.

These functions may return ``None`` if storage is not available as well as some
metadata such as storage creation timestamp ``_ctime`` and
last modification timestamp ``_mtime``.

Example:

.. code-block:: python

    def module_function(self):
        # set some storage
        self.py3.storage_set('my_key', value)
        # get the value or None if key not present
        value = self.py3.storage_get('my_key')


Module documentation
--------------------

All contributed modules should have correct documentation.  This documentation
is in a specific format and is used to generate user documentation.

The docstring of a module is used.  The format is as follows:

- Single line description of the module followed by a single blank line.

- Longer description of the module providing more detail.

- Configuration parameters.  This section describes the user settable
  parameters for the module.  All parameters should be listed (in alphabetical
  order). default values should be given in parentheses eg ``(default 7)``.

- Format placeholders.  These are used for substituting values in
  format strings. All placeholders should be listed (in alphabetical
  order) and describe the output that they provide.

- Color options.  These are the color options that can be provided for this
  module.  All color options should be listed (in alphabetical order) that the
  module uses.

- Requires.  A list of all the additional requirements for the module to work.
  These may be command line utilities, python libraries etc.

- Example.  Example configurations for the module can be given.

- Author and license.  Finally information on the modules author and a license
  can be provided.

Here is an example of a docstring.

.. code-block:: python

    """
    Single line summary

    Longer description of the module.  This should help users understand the
    modules purpose.

    Configuration parameters:
        parameter: Explanation of this parameter (default <value>)
        parameter_other: This parameter has a longer explanation that continues
            onto a second line so it is indented.
            (default <value>)

    Format placeholders:
        {info} Description of the placeholder

    Color options:
        color_meaning: what this signifies, defaults to color_good
        color_meaning2: what this signifies

    Requires:
        program: Information about the program
        python_lib: Information on the library

    Example:

    ```
    module {
        parameter = "Example"
        parameter_other = 7
    }
    ```

    @author <author>
    @license <license>
    """

Deprecation of configuration parameters
---------------------------------------

Sometimes it is necessary to deprecate configuration parameters.  Modules
are able to specify information about deprecation so that it can be done
automatically.  Deprecation information is specified in the Meta class of a
py3status module using the deprecated attribute.  The following types of
deprecation are supported.

The deprecation types will be performed in the order here.

**rename**

The parameter has been renamed.  We will update the configuration to use the
new name.

.. code-block:: python

    class Py3status:

        class Meta:

            deprecated = {
                'rename': [
                    {
                        'param': 'format_available',  # parameter name to be renamed
                        'new': 'icon_available',   # the parameter that will get the value
                        'msg': 'obsolete parameter use `icon_available`',  # message
                    },
                ],
            }

**format_fix_unnamed_param**

Some formats used ``{}`` as a placeholder this needs to be updated to a named
placeholder eg ``{value}``.

.. code-block:: python

    class Py3status:

        class Meta:

            deprecated = {
                'format_fix_unnamed_param': [
                    {
                        'param': 'format',  # parameter to be changed
                        'placeholder': 'percent',  # the place holder to use
                        'msg': '{} should not be used in format use `{percent}`',  # message
                    },
                ],
            }

**rename_placeholder**

We can use this to rename placeholders in format strings

.. code-block:: python

    class Py3status:

        class Meta:

            deprecated = {
                'rename_placeholder': [
                    {
                        'placeholder': 'cpu',  # old placeholder name
                        'new': 'cpu_usage',  # new placeholder name
                        'format_strings': ['format'],  # config settings to update
                    },
                ],
            }

**update_placeholder_format**

This allows us to update the format of a placeholder in format strings.
The key value pairs {placeholder: format} can be supplied as a dict in
``placeholder_formats`` or the dict can be provided by ``function`` the
function will be called with the current config and must return a dict.
If both are supplied then ``placeholder_formats`` will be updated using
the dict supplied by the function.

.. code-block:: python

    class Py3status:

        class Meta:

            deprecated = {
                'update_placeholder_format': [
                    {
                        'function': update_placeholder_format,  # function returning dict
                        'placeholder_formats': {   # dict of placeholder:format
                            'cpu_usage': ':.2f',
                        },
                        'format_strings': ['format'],  # config settings to update
                    }
                ],
            }

**substitute_by_value**

This allows one configuration parameter to set the value of another.

.. code-block:: python

    class Py3status:

        class Meta:

            deprecated = {
                'substitute_by_value': [
                    {
                        'param': 'mode',  # parameter to be checked for substitution
                        'value': 'ascii_bar',  # value that will trigger the substitution
                        'substitute': {
                            'param': 'format',  # parameter to be updated
                            'value': '{ascii_bar}',  # the value that will be set
                        },
                        'msg': 'obsolete parameter use `format = "{ascii_bar}"`',  #message
                    },
                ],
            }

**function**

For more complex substitutions a function can be defined that will be called
with the config as a parameter.  This function must return a dict of key value
pairs of parameters to update

.. code-block:: python

    class Py3status:

        class Meta:

            # Create a function to be called
            def deprecate_function(config):
                # This function must return a dict
                return {'thresholds': [
                            (0, 'bad'),
                            (config.get('threshold_bad', 20), 'degraded'),
                            (config.get('threshold_degraded', 50), 'good'),
                        ],
                }

            deprecated = {
                'function': [
                    {
                        'function': deprecate_function,  # function to be called
                    },
                ],
            }

**remove**

The parameters will be removed.

.. code-block:: python

    class Py3status:

        class Meta:

            deprecated = {
                'remove': [
                    {
                        'param': 'threshold_bad',  # name of parameter to remove
                        'msg': 'obsolete set using thresholds parameter',  #message
                    },
                ],
            }

Updating of configuration parameters
------------------------------------

Sometimes it is necessary to update configuration parameters.  Modules
are able to specify information about updates so that it can be done
automatically.  Config updating information is specified in the Meta class of a
py3status module using the update_config attribute.  The following types of
updates are supported.

**update_placeholder_format**

This allows us to update the format of a placeholder in format strings.
The key value pairs {placeholder: format} can be supplied as a dict in
``placeholder_formats`` or the dict can be provided by ``function`` the
function will be called with the current config and must return a dict.
If both are supplied then ``placeholder_formats`` will be updated using
the dict supplied by the function.

This is similar to the deprecation method but is to allow default formatting of
placeholders to be set.

In a module like sysdata we have placeholders eg ``{cpu_usage}`` this ends up
having a value something like ``20.542317173377157`` which is strange as the
value to use but gives the user the ability to have as much precision as they
want. A module writer may decide that they want this displayed as ``20.54`` so
``{cpu_usage:.2f}`` would do this. Having a default format containing that
just looks long/silly and the user setting a custom format just wants to do
``format = 'CPU: {cpu_usage}%'`` and get expected results ie not the full
precision. If they don't like the default formatting of the number they could
still do format = 'CPU: {cpu_usage:d}%' etc.

So using this allows sensible defaults formatting and allows simple
placeholders for user configurations.

.. code-block:: python

    class Py3status:

        class Meta:

            update_config = {
                'update_placeholder_format': [
                    {
                        'placeholder_formats': {   # dict of placeholder:format
                            'cpu_usage': ':.2f',
                        },
                        'format_strings': ['format'],  # config settings to update
                    }
                ],
            }

Module testing
--------------

Each module should be able to run independently for testing purposes.
This is simply done by adding the following code to the bottom of your module.

.. code-block:: python

    if __name__ == "__main__":
        """
        Run module in test mode.
        """
        from py3status.module_test import module_test
        module_test(Py3status)

If a specific config should be provided for the module test, this
can be done as follows.

.. code-block:: python

    if __name__ == "__main__":
        """
        Run module in test mode.
        """
        config = {
            'always_show': True,
        }
        from py3status.module_test import module_test
        module_test(Py3status, config=config)

Such modules can then be tested independently by running
``python /path/to/module.py``.

.. code-block:: bash

    $ python loadavg.py
    [{'full_text': 'Loadavg ', 'separator': False,
    'separator_block_width': 0, 'cached_until': 1538755796.0},
    {'full_text': '1.87 1.73 1.87', 'color': '#9DD7FB'}]
    ^C

We also can produce an output similar to i3bar output in terminal with
``python /path/to/module.py --term``.

.. code-block:: bash

    $ python loadavg.py --term
    Loadavg 1.41 1.61 1.82
    Loadavg 1.41 1.61 1.82
    Loadavg 1.41 1.61 1.82
    ^C
