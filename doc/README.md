
py3status documentation
=======================

[Using modules](#modules)

* [Available modules](#available_modules)
* [Ordering modules](#ordering_modules)
* [Configuring modules](#configuring_modules)
* [Py3status configuration section](#py3status_section)
* [Configuration obfuscation](#obfuscation)
* [Configuring colors](#configuring_color)
* [Configuring thresholds](#configuring_thresholds)
* [Grouping modules](#group_modules)

[Custom click events](#on_click)

* [Special on_click commands](#on_click_commands)
* [Module data and on_click commands](#on_click_data)

[Writing custom modules](#writing_custom_modules)

* [Example 1: Hello world](#example_1)
* [Example 2: Configuration parameters](#example_2)
* [Example 3: Events](#example_3)
* [Example 4: Status string placeholders](#example_4)
* [Example 5: Using color constants](#example_5)
* [Module methods](#module_methods)
* [Py3 module helper](#py3)
* [Composites](#composites)
* [Module documentation](#docstring)
* [Deprecation of configuration parameters](#deprecation)
* [Updating configuration parameters](#update_config)
* [Module testing](#testing)

[Contributing](#contributing)

***

<a name="modules"></a>Using modules
===================================

Modules in py3status are configured using your usual `i3status.conf`.

py3status tries to find the config in the following locations:
- `~/.i3/i3status.conf`,
- `~/.i3status.conf`,
- `/etc/i3status.conf`,
- `XDG_CONFIG_HOME/.config/i3status/config`,
- `~/.config/i3status/config`,
- `XDG_CONFIG_DIRS/i3status/config`,
- `/etc/xdg/i3status/config`,

You can also specify the config location using `py3status -c <path to config
file>` in your i3 configuration file.

#### <a name="available_modules"></a>Available modules
py3status comes with a large range of modules.

[List of available modules and their configuration details.](
https://github.com/ultrabug/py3status/blob/master/py3status/modules/README.md)

#### <a name="ordering_modules"></a>Loading a py3status module and ordering modules output


To load a py3status module you just have to list it like any other i3status
module using the `order +=` parameter.

Ordering your py3status modules in your i3bar is just the same as i3status
modules, just list the order parameter where you want your module to be
displayed.

For example you could insert and load the `imap` module like this:
```
order += "disk /home"
order += "disk /"
order += "imap"
order += "time"
```

#### <a name="configuring_modules"></a>Configuring a py3status module

Your py3status modules are configured the exact same way as i3status modules, directly from your `i3status.conf`, like this :
```
# configure the py3status imap module
# and run thunderbird when I left click on it
imap {
    cache_timeout = 60
    imap_server = 'imap.myprovider.com'
    mailbox = 'INBOX'
    password = 'coconut'
    port = '993'
    user = 'mylogin'
    on_click 1 = "exec thunderbird"
}
```

#### <a name="py3status_section"></a>py3status configuration section
This special section holds py3status specific configuration. Settings here
will affect all py3status modules.  Many settings e.g. colors can still be
overridden by also defining in the individual module.

Global options:

- `nagbar_font`. It will be used as an argument to
    `i3-nagbar -f`, thus setting its font.

    Example usage:
    ```
    py3status {
        nagbar_font = 'pango:Ubuntu Mono 12'
    }
    ```

#### <a name="obfuscation"></a>Configuration obfuscation

__New in version 3.1__

Py3status allows you to hide individual configuration parameters so that they
do not leak into log files, user notifications or to the i3bar. Additionally
they allow you to obfuscate configuration parameters using base64 encoding.

To do this you need to add an obfuscation option to the configuration
parameter. Obfuscation options are added by adding `:hide` or `:base64` to the
name of the parameters.
__Obfuscation is only available for string parameters.__

Example:

```
# normal_parameter will be shown in log files etc as 'some value'
# obfuscated_parameter will be shown in log files etc as '***'
module {
    normal_parameter = 'some value'
    obfuscated_parameter:hide = 'some value'
}
```

In the previous example configuration the users password is in plain text.
Users may want to make it less easy to read. Py3status allows strings to be
base64 encoded.

To use an encoded string add `:base64` to the name of the parameter.

```
# Example of obfuscated configuration
imap {
    imap_server = 'imap.myprovider.com'
    password:base64 = 'Y29jb251dA=='
    user = 'mylogin'
}
```

__Base64 encoding is very simple and should not be considered secure in any way.__

#### <a name="configuring_color"></a>Configuring colors

Since version 3.1 py3status allows greater color configuration.
Colors can be set in the general section of your `i3status.conf` or in an
individual modules configuration.  If a color is not in a modules configuration
the the values from the general section will be used.

If a module does not specify colors but it is in a container, then the colors
of the container will be used if they are set, before using ones defined in the
general section.

Example:
```
general {
    # These will be used if not supplied by a module
    color = '#FFFFFF'
    color_good = '#00FF00'
    color_bad = '#FF0000'
    color_degraded = '#FFFF00'
}

time {
    color = 'FF00FF'
    format = "%H:%M"
}

battery_level {
    color_good = '#00AA00'
    color_bad = '#AA0000'
    color_degraded = '#AAAA00'
    color_charging = '#FFFF00'
}
```

#### <a name="configuring_thresholds"></a>Configuring thresholds

Some modules allow you to define thresholds in a module.  These are used to
determine which color to use when displaying the module.  Thresholds are
defined in the config as a list of tuples. With each tuple containing a value
and a color. The color can either be a named color eg `good` referring to
`color_good` or a hex value.

Example:
```
volume_status {
    thresholds = [
        (0, "#FF0000"),
        (20, "degraded"),
        (50, "bad"),
    ]
}
```

If the value checked against the threshold is equal to or more than a threshold
then that color supplied will be used.

In the above example the logic would be

if 0 >= value < 20 use #FF0000
else if 20 >= value < 50 use color_degraded
else if 50 >= value use color_good


Some modules may allow more than one threshold to be defined.  If all the thresholds are the same they can be defined as above but if you wish to specify them separately you can by giving a dict of lists.

Example:
```
my_module {
    thresholds = {
        'threshold_1': [
            (0, "#FF0000"),
            (20, "degraded"),
            (50, "bad"),
        ],
        'threshold_2': [
            (0, "good"),
            (30, "bad"),
        ],
    }
}
```


#### <a name="group_modules"></a>Grouping Modules

The [group](
https://github.com/ultrabug/py3status/blob/master/py3status/modules/README.md#group
)
module allows you to group several modules together.  Only one of the
modules are displayed at a time.  The displayed module can either be cycled
through automatically or by user action (the default, on mouse scroll).

This module is very powerful and allows you to save a lot of space on your bar.
Example usage:
```
order += "group tz"

# cycle through different timezone hours every 10s
group tz {
    cycle = 10
    format = "{output}"

    tztime la {
        format = "LA %H:%M"
        timezone = "America/Los_Angeles"
    }

    tztime ny {
        format = "NY %H:%M"
        timezone = "America/New_York"
    }

    tztime du {
        format = "DU %H:%M"
        timezone = "Asia/Dubai"
    }
}
```

The [frame](
https://github.com/ultrabug/py3status/blob/master/py3status/modules/README.md#frame
)
module also allows you to group several modules together, however in a frame
all the modules are shown.  This allows you to have more than one module shown
in a group.
Example usage:
```
order += "group frames"

# group showing disk space or times using button to change what is shown.
group frames {
    click_mode = "button"

    frame time {
        tztime la {
            format = "LA %H:%M"
            timezone = "America/Los_Angeles"
        }

        tztime ny {
            format = "NY %H:%M"
            timezone = "America/New_York"
        }

        tztime du {
            format = "DU %H:%M"
            timezone = "Asia/Dubai"
        }
    }

    frame disks {
        disk "/" {
            format = "/ %avail"
        }

        disk "/home" {
            format = "/home %avail"
        }
    }
}
```

Frames can also have a toggle button to hide/show the content

Example:
```
# A frame showing times in different cities.
# We also have a button to hide/show the content

frame time {
    format = '{output}{button}'
    format_separator = ' '  # have space instead of usual i3bar separator

    tztime la {
        format = "LA %H:%M"
        timezone = "America/Los_Angeles"
    }

    tztime ny {
        format = "NY %H:%M"
        timezone = "America/New_York"
    }

    tztime du {
        format = "DU %H:%M"
        timezone = "Asia/Dubai"
    }
}
```

## <a name="on_click"></a>Custom click events

py3status allows you to easily add click events to modules in your i3bar.
These modules can be both i3status or py3status modules. This is done in
your `i3status.config` using the `on_click` parameter.

Just add a new configuration parameter named `on_click [button number]` to
your module config and py3status will then execute the given i3 command
(using i3-msg).

This means you can run simple tasks like executing a program or execute any
other i3 specific command.

As an added feature and in order to get your i3bar more responsive, every
`on_click` command will also trigger a module refresh. This works for both
py3status modules and i3status modules as described in the refresh command
below.

Examples:

```
# reload the i3 config when I left click on the i3status time module
# and restart i3 when I middle click on it
time {
    on_click 1 = "reload"
    on_click 2 = "restart"
}

# control the volume with your mouse (need >i3-4.8)
# launch alsamixer when I left click
# kill it when I right click
# toggle mute/unmute when I middle click
# increase the volume when I scroll the mouse wheel up
# decrease the volume when I scroll the mouse wheel down
volume master {
    format = "♪: %volume"
    device = "default"
    mixer = "Master"
    mixer_idx = 0
    on_click 1 = "exec i3-sensible-terminal -e alsamixer"
    on_click 2 = "exec amixer set Master toggle"
    on_click 3 = "exec killall alsamixer"
    on_click 4 = "exec amixer set Master 1+"
    on_click 5 = "exec amixer set Master 1-"
}

# run wicd-gtk GUI when I left click on the i3status ethernet module
# and kill it when I right click on it
ethernet eth0 {
    # if you use %speed, i3status requires root privileges
    format_up = "E: %ip"
    format_down = ""
    on_click 1 = "exec wicd-gtk"
    on_click 3 = "exec killall wicd-gtk"
}

# run thunar when I left click on the / disk info module
disk / {
    format = "/ %free"
    on_click 1 = "exec thunar /"
}

# this is a py3status module configuration
# open an URL on opera when I left click on the weather_yahoo module
weather_yahoo paris {
    cache_timeout = 1800
    woeid = 615702
    forecast_days = 2
    on_click 1 = "exec opera http://www.meteo.fr"
    request_timeout = 10
}
```

#### <a name="on_click_commands"></a>Special on_click commands

There are two commands you can pass to the `on_click` parameter that have a
special meaning to py3status :

*  `refresh` : This will refresh (expire the cache) of the clicked module.
   This also works for i3status modules (it will send a SIGUSR1 to i3status
   for you).

*  `refresh_all` : This will refresh all the modules from your i3bar
   (i3status included). This has the same effect has sending a SIGUSR1 to
   py3status.

#### <a name="on_click_data"></a>Module data and on_click commands

Since version 3.3 it is possible to use the output text of a module in the
`on_click` command.  To do this `$OUTPUT` can be used in command and it will be
substituted by the modules text output when the command is run.

Example:

```
# copy module output to the clipboard using xclip
my_module {
    on_click 1 = 'exec echo $OUTPUT | xclip -i'
}
```

If the output of a module is a composite then the output of the part clicked on
can be accessed using `$OUTPUT_PART`.

***

<a name="writing_custom_modules"></a>Writing custom py3status modules
=====================================================================

__This guide covers the new style of py3status modules. These are only
available in version 3.0 and above.__

Writing custom modules for py3status is easy. This guide will teach you how.

Let's start by looking at a simple example.

## <a name="example_1"></a>Example 1: The basics - Hello World!

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
            'cached_until': self.py3.CACHE_FOREVER
        }
```

####Running the example


Save the file as `hello_world.py` in a directory that
py3status will check for modules. By default it will look in
`$HOME/.i3/py3status/` or you can specify additional directories using
`--include` when you run py3status.

You need to tell py3status about your new module,
so in your `i3status.conf` add:
```
order += "hello_world"
```

Then restart i3 by pressing `Mod` + `Shift` + `R`. Your new module should now
show up in the status bar.

####How does it work?

The `Py3status` class tells py3status that this is a module. The module gets
loaded. py3status then calls any public methods that the class contains to get
a response. In our example there is a single method `hello_world()`.
Read more here: [module methods](#module_methods).

####The response

The response that a method returns must be a python `dict`.
It should contain at least two key / values.

######full_text

This is the text that will be displayed in the status bar.

######cached_until

This tells py3status how long it should consider your
response valid before it should re-run the method to get a fresh response. In
our example our response will not need to be updated so we can use the special
`self.py3.CACHE_FOREVER` constant. This tells py3status to consider our
response always valid.

`cached_until` should be generated via the `self.py3.time_in()` method.

####self.py3

This is a special object that gets injected into py3status
modules. It helps provide functionality for the module, such as the
`CACHE_FOREVER` constant. Read more here: [Py3 module helper](#py3)


## <a name="example_2"></a>Example 2: Configuration parameters

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
            'cached_until': self.py3.CACHE_FOREVER
        }
```
This module still outputs 'Hello World' as before but now you can customise the
output using your `i3status.config` for example to show the text in French.
```
hello_world {
    format = 'Bonjour tout le monde!'
}
```
In your module `self.format` will have been set to the value supplied in the
config.


## <a name="example_3"></a>Example 3: Click events

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
```

The `on_click` method of a module is special and will get
called when the module is clicked on. The event parameter
will be a dict that gives information about the event.

A typical event dict will look like this:
`{'y': 13, 'x': 1737, 'button': 1, 'name': 'example', 'instance': 'first'}`

You should only receive events for the module clicked on, so
generally we only care about the button.

The `__init__()` method is called when our class is instantiated. __Note: this
is called before any config parameters have been set.__

We use the `safe_format()` method of `py3` for formatting. Read more here: [Py3 module helper](#py3)

## <a name="example_4"></a>Example 4: Status string placeholders

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
```

This works just like the previous example but we can now be customised. The
following example assumes that our module has been saved as `click_info.py`.

```
click_info {
    format = "Cliquez ici"
    format_clicked = "Vous avez appuyé sur le bouton {button}"
}
```

## <a name="example_5"></a>Example 5: Using color constants

`self.py3` in our module has color constants that we can access, these allow the user to set colors easily in their config.

__Note: py3 colors constants require py3status 3.1 or higher__


```
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
            'cache_until': self.py3.CACHE_FOREVER
        }

    def on_click(self, event):
        # by defining on_click pressing any mouse button will refresh the
        # module.
        pass
```

The colors can be set in the config in the module or its container or in the
general section.  The following example assumes that our module has been saved
as `number.py`.  Although the constants are capitalized they are defined in the
config in lower case.

```
number {
    color_high = '#FF0000'
    color_low = '#00FF00'
}
```

***


## <a name="module_methods"></a>Module methods

Py3status will call a method in a module to provide output to the i3bar.
Methods that have names starting with an underscore will not be used in this
way.  Any methods defined as static methods will also not be used.

### Outputs

Output methods should provide a response dict.

Example response:

```
{
    'full_text': "This text will be displayed",
    'cached_until': 1470922537,  # Time in seconds since the epoch
}
```

The response can include the folowing keys

__cached_until__

The time (in seconds since the epoch) that the output will be classed as no longer valid and the output
function will be called again.

Since version 3.1, if no `cached_until` value is provided the the
output will be cached for `cache_timeout` seconds by default this is
`60` and can be set using the `-t` or `--timeout` option when running
py3status.  To never expire the `self.py3.CACHE_FOREVER` constant should be
used.

`cached_until` should be generated via the `self.py3.time_in()` method.

__color__

The color that the module output will be displayed in.

__composite__

Used to output more than one item to i3bar from a single output method.  If this is provided then `full_text` should not be.

__full_text__

This is the text output that will be sent to i3bar.

__index__

The index of the output.  Allows composite output to identify which component
of their output had an event triggered.

__separator__

If `False` no separator will be shown after the output block (requires i3bar
4.12).

__urgent__

If `True` the output will be shown as urgent in i3bar.


### Special methods

Some special method are also defined.

__kill()__

Called just before a module is destroyed.

__on_click(event)__

Called when an event is recieved by a module.

__post_config_hook()__

Called once an instance of a module has been created and the configuration
parameters have been set.  This is useful for any work a module must do before
its output methods are run for the first time. `post_config_hook()`
introduced in version 3.1

***


## <a name="py3"></a>Py3 module helper

Py3 is a special helper object that gets injected into
py3status modules, providing extra functionality.
A module can access it via the self.py3 instance attribute
of its py3status class.

#### Constants

__CACHE_FOREVER__

If this is returned as the value for `cached_until` then the module will not be
updated. This is useful for static modules and ones updating asynchronously.

__COLOR_&lt;VALUE&gt;__

Introduced in py3status version 3.1

This will have the value of the requested color as defined by the user config.
eg `COLOR_GOOD` will have the value `color_good` that the user had in their
config.  This may have been defined in the modules config, that of a container
or the general section.

Custom colors like `COLOR_CHARGING` can be used and are setable by the user in
their `i3status.conf` just like any other color.  If the color is undefined
then it will be the default color value.

#### Methods

__update(module_name=None)__

Update a module. If `module_name` is supplied the module of that
name is updated. Otherwise the module calling is updated.

__error(msg, timeout=None)__

Raise an error for the module.

`msg` message to be displayed explaining the error

`timeout` how long before we should retry.  For permanent errors
`py3.CACHE_FOREVER` should be returned.  If not supplied then the
modules `cache_timeout` will be used.

__is_color(color)__

Tests to see if a color is defined.
Because colors can be set to None in the config and we want this to be
respected in an expression like.

color = self.py3.COLOR_MUTED or self.py3.COLOR_BAD

The color is treated as True but sometimes we want to know if the color
has a value set in which case the color should count as False.  This
function is a helper for this second case.

Added in version 3.3

__is_python_2()__

True if the version of python being used is 2.x
Can be helpful for fixing python 2 compatability issues

__is_my_event(event)__

Checks if an event triggered belongs to the module recieving it.  This
is mainly for containers who will also recieve events from any children
they have.

Returns True if the event name and instance match that of the module
checking.

__format_units(value, unit='B', optimal=5, auto=True, si=False)__

Takes a value and formats it for user output, we can choose the unit to
use eg B, MiB, kbits/second.  This is mainly for use with bytes/bits it
converts the value into a human readable form.  It has various
additional options but they are really only for special cases.

The function returns a tuple containing the new value (this is a number
so that the user can still format it if required) and a unit that is
the units that we have been converted to.

By supplying unit to the function we can force those units to be used
eg `unit=KiB` would force the output to be in Kibibytes.  By default we
use non-si units but if the unit is si eg kB then we will switch to si
units.  Units can also be things like `Mbit/sec`.

If the auto parameter is False then we use the unit provided.  This
only makes sense when the unit is singular eg 'Bytes' and we want the
result in bytes and not say converted to MBytes.

optimal is used to control the size of the output value.  We try to
provide an output value of that number of characters (including decimal
point), it may also be less due to rounding.  If a fixed unit is used
the output may be more than this number of characters.

Added in version 3.3

__get_output(module_name)__

Return the output of the named module. This will be a list.

__trigger_event(module_name, event)__

Trigger an event on a named module.

__notify_user(msg, level='info', rate_limit=5)__

Send a notification to the user.
`level` must be `info`, `error` or `warning`.
`rate_limit` is the time period in seconds during which this message
should not be repeated.

__prevent_refresh()__

Calling this function during the on_click() method of a module will
request that the module is not refreshed after the event. By default
the module is updated after the on_click event has been processed.

__time_in(seconds=None, sync_to=None, offset=0)__

Returns the time a given number of seconds into the future.  Helpful
for creating the `cached_until` value for the module output.

Note: from version 3.1 modules no longer need to explicitly set a
`cached_until` in their response unless they wish to directly control it.

seconds specifies the number of seconds that should occure before the
update is required.

sync_to causes the update to be syncronised to a time period.  1 would
cause the update on the second, 60 to the nearest minute. By defalt we
syncronise to the nearest second. 0 will disable this feature.

offset is used to alter the base time used. A timer that started at a
certain time could set that as the offset and any syncronisation would
then be relative to that time.

__register_function(function_name, function)__

Register a function for the module.

The following functions can be registered

> __content_function()__
>
> Called to discover what modules a container is displaying.  This is
> used to determine when updates need passing on to the container and
> also when modules can be put to sleep.
>
> the function must return a set of module names that are being
> displayed.
>
> Note: This function should only be used by containers.
>
> __urgent_function(module_names)__
>
> This function will be called when one of the contents of a container
> has changed from a non-urgent to an urgent state.  It is used by the
> group module to switch to displaying the urgent module.
>
> `module_names` is a list of modules that have become urgent
>
> Note: This function should only be used by containers.

__format_contains(format_string, name)__

Determines if `format_string` contains placeholder `name`

`name` is tested against placeholders using fnmatch so the following
patterns can be used:

    * 	    matches everything
    ? 	    matches any single character
    [seq] 	matches any character in seq
    [!seq] 	matches any character not in seq

This is useful because a simple test like
`'{placeholder}' in format_string`
will fail if the format string contains placeholder formatting
eg `'{placeholder:.2f}'`

__get_placeholders_list(format_string, match=None)__

Returns a list of placeholders in `format_string`.

If `match` is provided then it is used to filter the result using
fnmatch so the following patterns can be used:

    * 	    matches everything
    ? 	    matches any single character
    [seq] 	matches any character in seq
    [!seq] 	matches any character not in seq

This is useful because we just get simple placeholder without any
formatting that may be applied to them
eg `'{placeholder:.2f}'` will give `['{placeholder}']`

__safe_format(format_string, param_dict=None, force_composite=False,
attr_getter=None)__

Parser for advanced formatting.

Unknown placeholders will be shown in the output eg `{foo}`

Square brackets `[]` can be used. The content of them will be removed
from the output if there is no valid placeholder contained within.
They can also be nested.

A pipe (vertical bar) `|` can be used to divide sections the first
valid section only will be shown in the output.

A backslash `\` can be used to escape a character eg `\[` will show `[`
in the output.

`\?` is special and is used to provide extra commands to the format
string,  example `\?color=#FF00FF`. Multiple commands can be given
using an ampersand `&` as a separator, example `\?color=#FF00FF&show`.

`{<placeholder>}` will be converted, or removed if it is None or empty.
Formating can also be applied to the placeholder eg
`{number:03.2f}`.

example format_string:

`"[[{artist} - ]{title}]|{file}"`
This will show `artist - title` if artist is present,
`title` if title but no artist,
and `file` if file is present but not artist or title.

param_dict is a dictionary of palceholders that will be substituted.
If a placeholder is not in the dictionary then if the py3status module
has an attribute with the same name then it will be used.

__Since version 3.3__

Composites can be included in the param_dict.


The result returned from this function can either be a string in the
case of simple parsing or a Composite if more complex.

If force_composite parameter is True a composite will always be
returned.

attr_getter is a function that will when called with a an attribute name
as a parameter will return a value.

__build_composite(format_string, param_dict=None, composites=None,
attr_getter=None)__

__deprecated in 3.3__ use safe_format()

Build a composite output using a format string.

Takes a format_string and treats it the same way as `safe_format` but
also takes a composites dict where each key/value is the name of the
placeholder and either an output eg `{'full_text': 'something'}` or a
list of outputs.

__composite_update(item, update_dict, soft=False)__

Takes a Composite (item) if item is a type that can be converted into a
Composite then this is done automatically.  Updates all entries it the
Composite with values from update_dict.  Updates can be soft in which
case existing values are not overwritten.

A Composite object will be returned.

__composite_join(separator, items)__

Join a list of items with a separator.
This is used in joining strings, responses and Composites.

A Composite object will be returned.

__composite_create(item)__

Create and return a Composite.

The item may be a string, dict, list of dicts or a Composite.

__is_composite(item)__

Check if item is a Composite and return True if it is.

__check_commands(cmd_list)__

Checks to see if the shell commands in list are available using `which`.
Returns the first available command.

If a string is passed then that command will be checked for.

__command_run(command)__

Runs a command and returns the exit code.
The command can either be supplied as a sequence or string.

An Exception is raised if an error occurs

__command_output(command)__

Run a command and return its output as unicode.
The command can either be supplied as a sequence or string.

An Exception is raised if an error occurs

__play_sound(sound_file)__

Plays sound_file if possible. Requires `paplay` or `play`.

__stop_sound()__

Stops any currently playing sounds for this module.

__threshold_get_color(value, name=None)__

Obtain color for a value using thresholds.

The value will be checked against any defined thresholds.  These should
have been set in the i3status configuration.  If more than one
threshold is needed for a module then the name can also be supplied.
If the user has not supplied a named threshold but has defined a
general one that will be used.

***


## <a name="composites"></a>Composites


Whilst most modules return a simple response eg:
```
{
    'full_text': <some text>,
    'cached_until': <cache time>,
}
```

Sometimes it is useful to provide a more complex, composite response.  A
composite is made up of more than one simple response which allows for example
a response that has multiple colors.  Different parts of the response can also
be differentiated between when a click event occures and so allow clicking on
different parts of the response to have different outcomes.  The different
parts of the composite will not have separators between them in the output so
they will appear as a single module to the user.

The format of a composite is as follows:

```
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
```

The `index` key in the response is used to identify the individual block and
when the the modules `on_click()` method is called the event will include this.
Supplied index values should be strings.  If no index is given then it will
have an integer value indicating its position in the composite.

***


## <a name="docstring"></a>Module documentation

All contributed modules should have correct documentation.  This documentation
is in a specific format and is used to generate user documentation.

The docsting of a module is used.  The format is as follows:

- Single line description of the module followed by a single blank line.

- Longer description of the module providing more detail.

- Configuration parameters.  This section describes the user setable
  parameters for the module.  All parameters should be listed (in alphabetical
  order). default values should be given in parentheses eg `(default 7)`.

- Format placeholders.  These are used for substituting values in
  format strings. All placeholders should be listed (in alphabetical
  order) and describe the output that they provide.

- Color options.  These are the color options that can be provided for this
  module.  All color options should be listed (in alphabetical order) that the
  module uses.

- Requires.  A list of all the additional requirements for the module to work.
  These may be command line utilities, python librarys etc.

- Example.  Example configerations for the module can be given.

- Author and license.  Finally information on the modules author and a license
  can be provided.

Here is an example of a docstring.

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

***

## <a name="deprecation"></a>Deprecation of configuration parameters

Sometimes it is necessary to deprecate configuration parameters.  Modules
are able to specify information about deprecation so that it can be done
automatically.  Deprecation information is specified in the Meta class of a
py3status module using the deprecated attribute.  The following types of
deprecation are supported.

The deprecation types will be performed in the order here.

__rename__

The parameter has been renamed.  We will update the configuration to use the
new name.

```
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
```

__format_fix_unnamed_param__

Some formats used `{}` as a placeholder this needs to be updated to a named
placeholder eg `{value}`.

```
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
```

__rename_placeholder__

We can use this to rename placeholders in format strings

```
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
```

__update_placeholder_format__

This allows us to update the format of a placeholder in format strings.
The key value pairs {placeholder: format} can be supplied as a dict in
`placeholder_formats` or the dict can be provided by `function` the
function will be called with the current config and must return a dict.
If both are supplied then `placeholder_formats` will be updated using
the dict supplied by the function.

```
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
```
__substitute_by_value__

This allows one configuration parameter to set the value of another.

```
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
```

__function__

For more complex substitutions a function can be defined that will be called
with the config as a parameter.  This function must return a dict of key value
pairs of parameters to update

```
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
```

__remove__

The parameters will be removed.

```
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
```

***

## <a name="update_config"></a>Updating of configuration parameters

Sometimes it is necessary to update configuration parameters.  Modules
are able to specify information about updates so that it can be done
automatically.  Config updating information is specified in the Meta class of a
py3status module using the update_config attribute.  The following types of
updates are supported.

__update_placeholder_format__

This allows us to update the format of a placeholder in format strings.
The key value pairs {placeholder: format} can be supplied as a dict in
`placeholder_formats` or the dict can be provided by `function` the
function will be called with the current config and must return a dict.
If both are supplied then `placeholder_formats` will be updated using
the dict supplied by the function.

This is similar to the deprecation method but is to allow default formatting of
placeholders to be set.

In a module like sysdata we have placeholders eg `{cpu_usage}` this ends up
having a value something like `20.542317173377157` which is strange as the
value to use but gives the user the ability to have as much precision as they
want. A module writer may decide that they want this displayed as `20.54` so
`{cpu_usage:.2f}` would do this. Having a default format containing that
just looks long/silly and the user setting a custom format just wants to do
`format = 'CPU: {cpu_usage}%'` and get expected results ie not the full
precision. If they don't like the default formatting of the number they could
still do format = 'CPU: {cpu_usage:d}%' etc.

So using this allows sensible defaults formatting and allows simple
placeholders for user configurations.

```
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
```

***

## <a name="testing"></a>Module testing

Each module should be able to run independantly for testing purposes.
This is simply done by adding the following code to the bottom of your module.

```
if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
```

If a specific config should should be provided for the module test, this
can be done as follows.

```
if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        'always_show': True,
    }
    from py3status.module_test import module_test
    module_test(Py3status, config=config)
```

Such modules can then be tested independently by running
`python path/to/module`

***

<a name="contributing"></a>Contributing
=======================================

Contributions to py3status either to the core code or for new or
existing modules are welcome.

# What you will need

- python3/python2
- i3status
    - http://i3wm.org/i3status/
    - https://github.com/i3/i3status
- pytest pytest-flake8
    - https://pypi.python.org/pypi/pytest
    - https://pypi.python.org/pypi/pytest-flake8

# Python versions

py3status code, including modules, should run under both python 2 and python 3.

# Pytest

Py3status uses pytest and the pytest-flake8 plugin for testing. All submissions
to the project must pass testing. To install these via pip use

```
pip install pytest
pip install pytest-flake8
```

The tests can be run by using `py.test --flake8` in the py3status root directory.

Tests are kept in the `tests` directory.

# Travis CI

When you create your Pull Request, some checks from Travis CI will
automatically run; you can see [previous
builds](https://travis-ci.org/ultrabug/py3status/) if you want to.

If something fails in the CI:

- Take a look the build log
- If you don't get what is failing or why it is failing, feel free to tell it
  as a comment in your PR: people here are helpful and open-minded :)
- Once the problem is identified and fixed, rebase your commit with the fix and
  push it on your fork to trigger the CI again

For reference, you can take a look at [this
PR](https://github.com/ultrabug/py3status/pull/193); you won't see the old
failed CI runs, but you'll get an idea of the PR flow.

# Coding in containers

Warning, by default (at least [on
Archlinux](https://projects.archlinux.org/svntogit/community.git/tree/trunk/i3status.install?h=packages/i3status#n2)),
i3status has cap\_net\_admin capabilities, which will make it fail with
`operation not permitted` when running inside a Docker container.

```
$ getcap `which i3status`
/usr/sbin/i3status = cap_net_admin+ep
```

To allow it to run without these capabilites (hence disabling some of the
functionnalities), remove it with:

```
setcap -r `which i3status`
```
